import streamlit as st
import pandas as pd
from io import StringIO
import re
import spacy
import io

st.set_page_config(
    page_title="Тест концептов"
)

st.title("Тест концептов")

st.info("Здесь можно обработать результаты теста концептов, проведенного на Pathway", 
        icon="💡")

with st.expander("Краткое описание"):
            st.write("Скрипт умеет обрабатывать типы вопросов: "
            "\n * Scale -- шкала. Рассчитывается оценка топ-2"
            "\n * Choice -- закpытый вопрос с одним или несколькими вариантами ответа. Ответы выводятся по убыванию частоты"
            "\n * Open question -- открытый вопрос. Выводится топ-20 наиболее частых слов" 
            "\n * Preference -- выбор медиа. Варианты выводятся по убыванию частоты"
            "\n\n Результаты формируются от завершенных анкет. "
            "Завершенными считаются анкеты, где есть ответ на последний вопрос, который не является открытым")


uploaded_files = st.file_uploader(
    "Загрузите файлы Excel", type='xlsx', accept_multiple_files=True)

if st.button("Запустить"):
    k = 0
    data = pd.DataFrame()

    for uploaded_file in uploaded_files:
        k+=1
        temp_data = pd.read_excel(uploaded_file, engine="openpyxl")
        temp_data["0_concept_n"] = k
        if k == 1:
            columns = temp_data.columns
        else:
            temp_data.columns = columns
        data = pd.concat([data, temp_data])

    cols = data.columns
    cols_to_drop = cols[cols.str.contains("other answers")]

    data.drop(columns=cols_to_drop, inplace = True)

    def f1(string):
        return not(any(i.isdigit() for i in string))

    cols = data.columns
    idx = [f1(item) for item in cols]
    cols_to_drop = cols[idx]

    data.drop(columns=cols_to_drop, inplace = True)
    cols = data.columns
    data.reset_index(drop = True, inplace = True)

    open_qst = cols[cols.str.contains("Open question")]
    choice = cols[cols.str.contains("Choice")]
    scale = cols[cols.str.contains("Scale")]
    preference = cols[cols.str.contains("Preference")]
    choice = choice.append(preference)

    for i in cols:
         if "Open question" not in i and "0_concept_n" not in i:
              last_q = i

    data = data.loc[data[last_q].notna()]

    results = pd.DataFrame()

# вопросы с выбором ответа
    for i in choice:
         try:
             answers = data.loc[data[i].notna(), i]
             answers = answers.str.replace(")", "")
             answers = answers.str.replace("(","")
             answers = answers.str.replace("\n","")
             ans_list = (";").join(answers.astype(str))
             ans = list(set(ans_list.split(";")))
             for j in ans:
                 data[j] = answers.str.contains(j)
             ans.append("0_concept_n")
             temp = data[ans].groupby("0_concept_n").sum().T
             temp["Среднее по концептам"] = temp.sum(axis = 1)
             bases = list(data.groupby("0_concept_n").count()[ans[0]])
             bases.append(sum(bases))
             temp.index.name = "Ответы"
             temp["Вопрос"] = i
             temp = temp.set_index("Вопрос", append=True)
             temp = temp.swaplevel()
             temp = temp / bases
             temp["№"] = int(i.split(".")[0])
             temp.sort_values(by="Среднее по концептам", ascending=False, inplace = True)
             results = pd.concat([results, temp])
             
         except:
             st.error(f"Возникла проблема с обработкой вопроса **{i}**")
            
# шкальные вопросы
    nums = []
    temp_res = pd.DataFrame()
    for i in scale:
        temp_data = data.loc[data[i].notna(), [i, "0_concept_n"]]
        temp_data[i].astype('int64')
        if min(temp_data[i]) < 0:
            temp_data[i] = temp_data[i].replace([-2, -1, 0], 0)
            temp_data[i] = temp_data[i].replace([1, 2], 1)
        else:
            temp_data[i] = temp_data[i].replace([1, 2, 3], 0)
            temp_data[i] = temp_data[i].replace([4, 5], 1)
        temp = temp_data.groupby("0_concept_n").sum().T
        temp["Среднее по концептам"] = temp.sum(axis = 1)
        bases = list(temp_data.groupby("0_concept_n").count()[i])
        bases.append(sum(bases))
        temp.index.name = "Вопрос"
        temp["Ответы"] = "Топ-2 (оценки 4-5)"
        temp = temp.set_index("Ответы", append=True)
        temp = temp / bases
        num = i.split(".")[0]
        nums.append(int(num))
        temp_res = pd.concat([temp_res, temp], axis = 0)

    temp_res["№"] = nums
    results = pd.concat([results, temp_res], axis = 0)
    results.sort_values(by=["№", "Среднее по концептам"], ascending=[True, False], inplace = True)
        
    # обработка текста
    temp = pd.DataFrame(columns = results.columns, index = [open_qst])
    nlp = spacy.load('ru_core_news_lg')
    for i in open_qst:
        texts = data.loc[data[i].notna(), i]
        doc = nlp(" ".join(texts.astype(str)).lower())
        keywords_freq = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
        keywords = {}
        for key in keywords_freq:
            if not keywords.get(key, False):
                keywords[key] = 1
            else:
                keywords[key] += 1
        sorted_keys = dict(sorted(keywords.items(), key=lambda item: item[1], reverse = True))
        frq_fin = pd.DataFrame(data = sorted_keys, index = ["Частота"]).T
        frq_fin["Слово"] = frq_fin.index
        frq_fin.index = [i for i in range(len(frq_fin))]
        temp["Среднее по концептам"][i] = (", ").join(frq_fin[:20]["Слово"])
        n_con = list(data["0_concept_n"].unique())
        for j in n_con:
            data_temp = data.loc[data["0_concept_n"] == j]
            texts = data_temp.loc[data_temp[i].notna(), i]
            doc = nlp(" ".join(texts.astype(str)).lower())
            keywords_freq = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
            keywords = {}
            for key in keywords_freq:
                if not keywords.get(key, False):
                    keywords[key] = 1
                else:
                    keywords[key] += 1
            sorted_keys = dict(sorted(keywords.items(), key=lambda item: item[1], reverse = True))
            frq_fin = pd.DataFrame(data = sorted_keys, index = ["Частота"]).T
            frq_fin["Слово"] = frq_fin.index
            frq_fin.index = [k for k in range(len(frq_fin))]
            temp[j][i] = (", ").join(frq_fin[:20]["Слово"])
    nums = []
    for i in open_qst:
         num = i.split(".")[0]
         nums.append(int(num))
    temp["№"] = nums
    temp.index.name = "Вопрос"
    temp["Ответы"] = "Топ-20 слов"
    temp = temp.set_index("Ответы", append=True)

    results = pd.concat([results, temp], axis = 0)
    results.sort_values(by=["№", "Среднее по концептам"], ascending=[True, False], inplace = True)
    results.drop(columns=["№"], inplace=True)
    
    bases = list(data.groupby("0_concept_n").count()[last_q])
    bases.append(sum(bases))
    bases_pd = pd.DataFrame(index = results.columns, columns = ["Количество ответов"])
    bases_pd["Количество ответов"] = bases
    bases_pd = bases_pd.T
    bases_pd.index.name = "Вопрос"
    bases_pd["Ответы"] = ""
    bases_pd = bases_pd.set_index("Ответы", append=True)

    results = pd.concat([results, bases_pd], axis = 0)

    col = results.pop('Среднее по концептам')
    results.insert(0, col.name, col)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    # Write each dataframe to a different worksheet.
        results.to_excel(writer, merge_cells = True)
        writer.close()

    st.download_button(
        label="Скачать результаты",
        data=buffer,
        file_name="test_results.xlsx",
        mime="application/vnd.ms-excel"
    )
