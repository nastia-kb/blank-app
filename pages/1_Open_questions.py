import pandas as pd
import numpy as np
import spacy
import streamlit as st
from io import StringIO
import re
import io
import matplotlib
import matplotlib.pyplot as plt
from wordcloud import WordCloud

st.set_page_config(
    page_title="Тест концептов"
)

st.title("Обработка открытых")

st.info("Здесь можно обработать ответы на открытый вопрос и построить облако слов", 
        icon="💡")

with st.expander("Краткое описание"):
            st.write("Скрипт разделит тексты на отдельные слова, приведет их к начальной форме (единственное число, именительный падеж, мужской род) и посчитает частоту их упоминаний по всем ответам."
            "\n\n Облако слов можно построить опционально.")


uploaded_file = st.file_uploader(
    "Загрузите файлы Excel", type='xlsx', accept_multiple_files=False)

cloud = st.checkbox("Нужно облако слов")

if st.button("Запустить"):
        data = pd.read_excel(uploaded_file)
        texts = data.loc[data[data.columns[0]].notna(), data.columns[0]]
        texts.index = [i for i in range(len(texts))]

        nlp = spacy.load('ru_core_news_lg')
        doc = nlp(" ".join(texts.astype("str")).lower())

        keywords_freq = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
        keywords = {}
        for key in keywords_freq:
            if not keywords.get(key, False):
                keywords[key] = 1
            else:
                keywords[key] += 1
        sorted_keys = dict(sorted(keywords.items(), key=lambda item: item[1], reverse = True))

        table = pd.DataFrame([sorted_keys]).T

        if cloud == True:
            wordcloud = WordCloud(width = 2000,
                                height = 1500,
                                random_state=1,
                                background_color='white',
                                margin=20,
                                colormap="summer",
                                collocations=False).generate((" ").join(keywords_freq))

            fig = plt.figure(figsize=(40, 30))
            plt.imshow(wordcloud)
            plt.axis("off")
        
            st.pyplot(fig)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            table.to_excel(writer)
            writer.close()

        st.download_button(
            label="Скачать результаты",
            data=buffer,
            file_name="open_questions.xlsx",
            mime="application/vnd.ms-excel"
        )
