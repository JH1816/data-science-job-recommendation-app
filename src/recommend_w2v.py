from gensim.models.word2vec import Word2Vec
from gensim.models import word2vec
import pandas as pd
import copy
import numpy as np
from numpy.linalg import norm


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
def recommend(user_vector,items_num, job_vectors_string):
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
    num = min(items_num,  len(indexs))
    return indexs[:num]


# filter based on job title
def filter_job_title(df, job_title):
    if len(job_title)==0:
        return df
    for job in job_title:
        if job.lower() == "all":
            return df
    indexs = []
    for i in df.index:
        for title in job_title:
            if title.lower() in df.iloc[i]["job-title"].lower():
                indexs.append(i)
                continue
    return df.iloc[indexs]


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


if __name__=="__main__":

    model = Word2Vec.load("words200.model")

    # read in vector_added data
    df_data = pd.read_csv('/Users/cx/Documents/dsa3101-2210-05-data-science/src/vector_added200.csv')
    # select from a list of skills
    equipped_skills = [ "python", "SQL", "Powerbi", "tableau", "data analysis" ]
    new_skills = ["computer vision"]
    # select from a list of job title, (add "all" in front-end)
    job_title = ["data analyst", "data engineer"]
    # select from a list of industries, (add "all" in front-end)
    industries = ["Finance", "Healthcare"]

    # job title filter
    df_data_job = filter_job_title(df_data, job_title).reset_index()

    # industries filter
    df_data_filter_all = filter_industry(df_data_job, industries).reset_index()

    # decided on the number of recommendations
    items_num = 50

    # output user equipped skills vectors
    user_equipped_vector = user_skill_vector(equipped_skills, model)

    # output user new skills vectors
    user_new_vector = user_skill_vector(new_skills, model)

    # recommend job listings based on user already equipped skills
    indexs = recommend(user_equipped_vector, items_num, df_data_filter_all["job_vector"])

    # recommend job listings based on new skill user would like to learn
    indexs = recommend(user_new_vector, items_num, df_data_filter_all["job_vector"])

    urls_list = df_data["url"].iloc[indexs]
    print(urls_list.to_list())

    