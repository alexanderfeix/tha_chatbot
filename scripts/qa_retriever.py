import os


def get_data(filepath: str):
    """
    Retrieves data from the question-answer set.
    :param filepath: The path to the question-answer set folder.
    :return: A dictionary with questions as keys and answers as values.
    """
    questions, answers = [], []
    for file in os.listdir(filepath):
        with open(os.path.join(filepath, file)) as f:
            data = ""
            file_source = ""
            is_question = True
            for line in f:
                if line.startswith("# Source: "):
                    file_source = line.split("# Source: ")[1]
                    continue
                elif line.startswith("# "):
                    continue
                elif line.startswith("Q: "):
                    if not is_question:
                        if "https://" not in data and file_source != "":
                            data += f" Find more information here: {file_source}"
                        answers.append(data[3:].replace("\n", "").replace("    ", " "))  # passage:
                        data = ""
                        is_question = True
                elif line.startswith("A: "):
                    if is_question:
                        questions.append(data[3:].replace("\n", "").replace("    ", " ") + " ")  # query:
                        data = ""
                        is_question = False
                data += line
            if "https://" not in data and file_source != "":
                data += f" Find more information here: {file_source}"
            answers.append(data[3:].replace("\n", "").replace("    ", " "))
    return dict(zip(questions, answers))


def get_data_in_html_format(filepath: str):
    """
    Get the question-answer set in a format that can be used with Cohere RAG.
    :param filepath: The path to the data folder, containing the question-answer set folder.
    :return: A list of dictionaries with 'title', 'text', and 'url' keys.
    """
    data = get_data(os.path.join(filepath, "question_answer_set")) 
    html_data = []
    for key, value in data.items():
        html_data.append(
            {
                "title": key,
                "text": value,
                "url": "https://tha.de/"
            }
        )
    return html_data

