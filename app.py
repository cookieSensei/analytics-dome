import numpy as np
import pandas as pd
import plotly.express as px
import os
import re
from dash import Dash, Input, Output, dcc, html
import seaborn as sns




df = pd.read_csv("quiz_results_export.csv")

ch8211 = "–"

df["quiz_name"] = df["quiz_name"].apply(lambda x: re.sub(ch8211, "-", x))

# for i in df["quiz_name"]:
#     if ch8211 in i:
#         print("here")
#

def clean_quiz(txt):
    txt = txt.lower()
    txt = re.sub("copy -", "", txt).strip()
    txt = re.sub("grade ", "", txt).strip()
    txt = re.sub("sci ", "science ", txt)
    return txt

quiz = df["quiz_name"].apply(clean_quiz)

quiz_name_categories = quiz.value_counts().sort_index()
#
# for i in range(len(quiz_name_categories)):
#     print(quiz_name_categories.index[i], " "*30, ">>>>", quiz_name_categories[i])

# "- d[a-z]{0,5}.{0,2}[0-9][a-z]{0,1}"

def clean_branch(txt):
    txt = txt.lower()

    pattern = "- d[a-z]{0,5}.{0,2}[0-9][a-z]{0,1}|-d[a-z]{0,5}.{0,2}[0-9][a-z]{0,1}|d[0-9]|[0-9][a-z]"

    try:
        out = re.findall(pattern, txt)[0].upper()
        out = re.sub("-", "", out).strip()
        out = re.sub("DAR", "D", out)
        out = re.sub(" ", "", out)
        if len(out) == 2:
            if re.search("[0-9][A-Z]", out):
                out = "D" + out

    except:
        out = "branch_missing"
    return out


branch = quiz.apply(lambda x: clean_branch(x))

# display(branch.value_counts(dropna=False).sort_index())

df["school_branch"] = branch


def combine_branch_D5(txt):
    if txt == "D5A" or txt == "D5B":
        txt = "D5"
    return txt


df["school_branch"] = df["school_branch"].apply(combine_branch_D5)

# display(df["school_branch"].value_counts(dropna=False).sort_index())


def clean_subject_grade(txt):
    for i in ["kinder", "toddler", "nursery"]:
        if re.search(i, txt):
            grade = i
            txt = txt.split("-")[0]
            subject = txt.split(i)[0].strip()
            return subject, grade
    else:
        txt = txt.split("-")[0]
        subject = re.findall(r"[a-z\.\s]+", txt)[0].strip()
        grade = re.findall(r"[a-z\.\s]+ ([0-9]{1,2})", txt)

        try:
            grade = grade[0]

        except:
            grade = np.nan
        return subject, grade


subject, grade = quiz.apply(lambda x: clean_subject_grade(x)[0]), quiz.apply(lambda x: clean_subject_grade(x)[1])

# subject.value_counts(dropna=False).sort_index()

# grade.value_counts(dropna=False).sort_index()

df["subject"] = subject
df["grade"] = grade

# df.head(2)


def get_score(txt):
    try:
        scored, total = txt.split("of")
        scored, total = float(scored), float(total)
    except:
        scored, total = np.nan, np.nan

    return scored, total


scored = []
total = []

for i in df["points"]:
    scored.append(get_score(i)[0])
    total.append(get_score(i)[1])

df["points_scored"] = scored
df["points_total"] = total

# df.head(2)

df["start_date"] = pd.to_datetime(df["start_date"], format="%Y-%m-%d %H:%M:%S")

df["end_date"] = pd.to_datetime(df["end_date"], format="%Y-%m-%d %H:%M:%S")

df["end-start"] = df.apply(lambda row: row["end_date"] - row["start_date"], axis=1)

# df.head(2)

df["date_wo_time"] = pd.to_datetime(df["start_date"].dt.date)
# df.head()


def clean_duration(txt):
    try: out = float(re.findall("(.+)s", txt)[0])
    except: out = txt
    return out


df["duration_seconds"] = df["duration"].apply(clean_duration)
# df.head(2)


df2 = df[["user", 'quiz_name', 'start_date', 'end_date', "end-start",
       'score', 'duration_seconds', 'points_scored', 'points_total',
         'school_branch', 'subject', 'grade', "date_wo_time"]]

# df2.head(2)


df2["grade"] = df2["grade"].fillna("unavailable")

############################################################
############################################################
############################################################

app = Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H1("Analytics Dome Median comaprison"),
        dcc.Graph(
            id="compare_brach",
            figure=px.bar(df2.groupby("school_branch")["score"].median())),
        dcc.Graph(figure=px.line(df2.groupby(["school_branch", "date_wo_time"]).median("score").reset_index(),
                                 x="date_wo_time", y="score", color="school_branch"))
    ]),

    html.Div([
        html.H1("Analytics Dome Student Count"),
        dcc.Graph(
            id="compare_count_brach",
            figure=px.bar(df2.groupby("school_branch")["score"].count())),
        dcc.Graph(figure=px.line(df2.groupby(["school_branch", "date_wo_time"]).median("score").reset_index(),
                                 x="date_wo_time", y="score", color="school_branch"))
    ]),

    html.Div([
        html.H1("Frequency distribution of score among selected brach and class"),
        dcc.Dropdown(id="dropdown_branch", options=df2["school_branch"].unique(), value="D5"),
        dcc.Dropdown(id="dropdown_grade", options=df2["grade"].unique(), value="10"),
        dcc.Dropdown(id="dropdown_subject", options=df2["subject"].unique(), value="science"),

        dcc.Graph(id="score_visual")
    ])

])


@app.callback(
    Output("score_visual", "figure"),
    Input("dropdown_branch", "value"),
    Input("dropdown_grade", "value"),
    Input("dropdown_subject", "value")
)
def plotly_interactive(branch, grade, subject):
    df = df2.copy()
    df = df.query(f"school_branch=='{branch}'")
    df = df.query(f"grade=='{grade}'")
    df = df.query(f"subject=='{subject}'")

    figure = px.histogram(df, x="score")
    return figure


if __name__ == "__main__":
    app.run(debug=False)





















