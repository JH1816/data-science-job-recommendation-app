from flask import Flask, request, jsonify, send_file, render_template, make_response
from werkzeug.utils import secure_filename

import numpy as np
from numpy.linalg import norm
import pandas as pd
import copy

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from gensim.models.word2vec import Word2Vec

import joblib
from waitress import serve

app = Flask(__name__)

# get user skills vector
def user_skill_vector(user_skills, model):
    for i in range(len(user_skills)):
        user_skills[i] = user_skills[i].lower()

    user_vector = None
    for skill in user_skills:
        words_of_skills = skill.split(" ")
        for word in words_of_skills:
            if word in model.wv.index_to_key:
                word_vector = copy.deepcopy( model.wv.get_vector(word) )
                if user_vector is None:
                    user_vector = word_vector
                else:
                    user_vector += word_vector

    return user_vector

# get cosine similarity
def get_similarity(vector1,vector2):
    return np.dot(vector1,vector2)/(norm(vector1)*norm(vector2))

# recommendation engine
def recommend(user_vector, job_vectors_string):
    similar_values = []
    for job_vector_string in job_vectors_string:
        job_vector_string_list = job_vector_string.split(" ")
        job_vector = []
        for num_string in job_vector_string_list:
            if num_string=="" or num_string=="[" or num_string=="]":
                continue
            job_vector.append(float(num_string.replace("\n","").replace("]","").replace("[","")))
        # job_vector = list(map(float,job_vector[1:-1]))
        # print("job user:",job_vector)
        # print("type of user skill:", type(user_vector))
        similar_value = get_similarity(job_vector,user_vector)
        similar_values.append(similar_value)

    indexs = np.argsort(-np.array(similar_values))
    # num = min(items_num,  len(indexs))
    return indexs

# filter based on job title
def filter_job_title(df, job_title):
    # if len(job_title)==0:
    #     return df
    # for job in job_title:
    #     if job.lower() == "all":
    #         return df
    # indexs = []
    # for i in df.index:
    #     for title in job_title:
    #         if title.lower() in df.iloc[i]["job-title"].lower():
    #             indexs.append(i)
    #             continue
    # return df.iloc[indexs]
    return df[df["normalized_title"].isin(job_title)]


# filter based on industries
def filter_industry(df, industries):
    if len(industries)==0:
        return df
    for industry in industries:
        if industry.lower() == "all":
            return df
    indexs = []
    for i in df.index:
        for industry in industries:
            if df.iloc[i][industry]:
                indexs.append(i)
                continue
    return df.iloc[indexs]

def get_cos_scores(vectorizer, JD_tfidf, skills):
    """Returns the cosine similarity score for the given skills of the user"""
    skills_tfidf = vectorizer.transform(skills)
    cos_similarity_tfidf = map(lambda x: cosine_similarity(skills_tfidf, x), JD_tfidf)
    scores = list(cos_similarity_tfidf)
    scores = list(map(lambda score: score.flatten()[0], scores))
    idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    
    return scores, idx

def get_KNN_scores(vectorizer, JD_tfidf, skills):
    KNN = NearestNeighbors()
    KNN.fit(JD_tfidf)
    NN = KNN.kneighbors(vectorizer.transform([" ".join(skills)]), n_neighbors=JD_tfidf.shape[0])
    scores = NN[0][0]
    idx = NN[1][0]
    
    return scores, idx

def min_max_scaling(lst):
    return (lst - min(lst)) / (max(lst) - min(lst))

def flip_knn_scores(scores):
    """To be comparable with cosine similarity score (bigger -> better)"""
    return 1 - scores

# -d '{"current_skills": ["Python", "Tableau"], "new_skills": ["R", "Azure"], "job_portal": "indeed"}'
# http://127.0.0.1:5001/recommendations
@app.route("/recommendations", methods=["GET", "POST"])
def get_recommendations():
    arguments = request.get_json()
    current_skills = arguments["current_skills"]
    new_skills = arguments["new_skills"]
    all_skills = current_skills + new_skills
    job_portal = arguments["job_portal"].lower()
    job_title = arguments["job_title"]
    job_title = [title.lower() for title in job_title]

    if job_portal == "indeed":
        JD_tfidf, tfidf_vectorizer = joblib.load("indeed_tfidf.pkl")
        indeed_df = joblib.load("indeed_data.pkl")

        # get the scores for both similarity measures
        cosine_scores, cosine_idx = get_cos_scores(tfidf_vectorizer, JD_tfidf, all_skills)
        knn_scores, knn_idx = get_KNN_scores(tfidf_vectorizer, JD_tfidf, all_skills)

        # normalize the scores before combining
        cosine_scores = min_max_scaling(cosine_scores)
        knn_scores = min_max_scaling(knn_scores)
        knn_scores = flip_knn_scores(knn_scores)

        # for cosine
        df_with_cosine_scores = indeed_df.assign(score=cosine_scores)
        indeed_df_cosine = df_with_cosine_scores.iloc[cosine_idx,:]

        # for knn
        indeed_df_sorted = indeed_df.iloc[knn_idx,:]
        indeed_df_knn = indeed_df_sorted.assign(score=knn_scores)

        # get average scores for both methods
        cosine_df_scores = indeed_df_cosine.loc[:, "score"]
        combined_df = indeed_df_knn.join(cosine_df_scores, rsuffix="_cosine")
        combined_df["average_score"] = combined_df.apply(lambda x: (x["score"] + x["score_cosine"]) / 2, axis=1)
        sorted_df = combined_df.sort_values("average_score", ascending=False)

       
        # filter for job titles
        filtered_df = sorted_df[sorted_df["normalized_title"].isin(job_title)]
        
        return filtered_df.reset_index(drop=True).to_json()

    elif job_portal == "jobsdb":
        model = Word2Vec.load("words200_v2.model")
        df = joblib.load("jobsdb_data.pkl")

        # select from a list of industries, (add "all" in front-end)
        # industries = ["Finance", "Healthcare"]
        
        # job title filter
        df_data_job = filter_job_title(df, job_title).reset_index()

        # industries filter
        # df_data_filter_all = filter_industry(df_data_job, industries).reset_index()

        user_vector = user_skill_vector(all_skills, model)

        indexs = recommend(user_vector, df_data_job["job_vector"])

        recommendations = df.iloc[indexs, [0,1,2,3,4,5]]

        return recommendations.to_json()
    else:
        return "FAIL"

@app.route("/", methods=["GET"])
def test_func():
    return "API running"

def create_app():
    return app

# if __name__ == "__main__":
#     serve(app, host="0.0.0.0", port=8080)