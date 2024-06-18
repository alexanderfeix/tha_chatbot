from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from spellchecker import SpellChecker

bachelor_links_english = {
    "architecture": [
        "https://www.tha.de/Binaries/Binary_37263/Architektur-BA-MA-SPO-2019-C-Studienverlauf.pdf",
        "More information here: https://www.tha.de/en/Architecture-and-Civil-Engineering/Architecture-BA.html"],

    "business administration": [
        "https://www.tha.de/Binaries/Binary68290/Betriebswirtschaft-BW-Modulhandbuch-abWiSe2023-24.pdf",
        "More information here: https://www.tha.de/Wirtschaft/Betriebswirtschaft-Bachelor.html"],

    "business psychology": ["./backend/rasa/actions/images/business-psychology1.webp",
                            "./backend/rasa/actions/images/business-psychology2.webp",
                            "./backend/rasa/actions/images/business-psychology3.webp",
                            "More information here: https://www.tha.de/Wirtschaft/Wirtschaftspsychologie.html"],

    "civil engineering": ["https://www.tha.de/Binaries/Binary72332/Bauingenieurwesen.mp4",
                          "More information here: https://www.tha.de/en/Architecture-and-Civil-Engineering/Civil-Engineering-BEng.html"],

    "communication design": ["./backend/rasa/actions/images/communication-design.webp",
                             "More information here: https://www.tha.de/en/Design/Communication-Design-BA.html"],

    "computer engineering": ["./backend/rasa/actions/images/computer-engineering.png",
                             "More information here: https://www.tha.de/en/Computer-Science/Computer"
                             "-Engineering-BEng.html"],

    ("computer science", "cs", "informatic", "informatics"): [
        "./backend/rasa/actions/images/computer-science.webp",
        "More information here: https://www.tha.de/en/Computer-Science/Computer-Science-BSc.html"],

    "creative engineering": ["./backend/rasa/actions/images/creative-engineering.webp",
                             "More information here: https://www.tha.de/Gestaltung/Creative-Engineering.html"],

    "data science": ["./backend/rasa/actions/images/data-science.webp",
                     "More information here: https://www.tha.de/Geistes-und-Naturwissenschaften/Data-Science"
                     ".html"],

    ("digital design and production", "digital design", "design and production"): [
        "./backend/rasa/actions/images/digital-design.webp",
        "More information here: https://www.tha.de/Architektur-und-Bauwesen/Digitaler-Baumeister-Bachelor.html"],

    "electrical engineering": ["https://www.tha.de/Binaries/Binary_13160/Studienplan-ElektrotechnikEA-IK.pdf",
                               "More information here: https://www.tha.de/en/Electrical-Engineering/Electrical-Engineering-BEng.html"],

    ("energy efficient planning and building", "energy planning", "planning and building of energy"): [
        "./backend/rasa/actions/images/energy-efficient-planning.jpg",
        "More information here: https://www.tha.de/en/Architecture-and-Civil-Engineering/Page19903.html"],

    ("environmental process engineering", "environmental engineering"): [
        "./backend/rasa/actions/images/environmental-process-engineering.webp",
        "More Information here: https://www.tha.de/en/Mechanical-and-Process-Engineering/bu-EN.html"],

    "industrial engineering": ["./backend/rasa/actions/images/industrial-engineering.webp",
                               "More information here: https://www.tha.de/en/Liberal-Arts-and-Sciences/Industrial-Engineering-BEng.html"],

    "information systems": ["./backend/rasa/actions/images/information-systems.webp",
                            "More information here: https://www.tha.de/en/Computer-Science/Information-Systems-BSc.html"],

    ("interactive media", "media"): [
        "./backend/rasa/actions/images/interaktive_mediensysteme.webp",
        "More information here: https://www.tha.de/en/Design/Interactive-Media/Interactive-Media-BA-BSc.html"],

    ("international information systems", "iis"): [
        "./backend/rasa/actions/images/international-information-systems.png",
        "More information here: https://www.tha.de/en/Computer-Science/International-Information-Systems-BSc.html"],

    ("international management", "management"): [
        " https://www.tha.de/Binaries/Binary29943/MHB-IM-SPO2016-WiSe21-22.pdf",
        "More information here: https://www.tha.de/Wirtschaft/International-Management-Bachelor.html"],

    ("international management and engineering", "international management engineering"): [
        "https://www.tha.de/Binaries/Binary38277/230918-Modulhandbuch-IWI-fuer-SPO-2016.pdf",
        "More information here: https://www.tha.de/en/Electrical-Engineering/International-Management-and-Engineering-BEng.html"],

    ("mechanical engineering", "mechanics", "mechanic"): [
        "./backend/rasa/actions/images/mechanical-engineering.webp",
        "More information here: https://www.tha.de/en/Mechanical-and-Process-Engineering/bm-EN.html"],

    ("mechatronics", "mechatronic"): ["https://www.tha.de/Binaries/Binary28103/Studienplan-Mechatronik-neu-korr.pdf",
                                      "More information here: https://www.tha.de/en/Electrical-Engineering/Page44656.html"],

    "social work": [
        "./backend/rasa/actions/images/social-work.webp",
        "More information here: https://www.tha.de/en/Liberal-Arts-and-Sciences/Social-Work.html"],

    "systems engineering": [
        "./backend/rasa/actions/images/systems-engineering.webp",
        "More information here: https://www.tha.de/en/Computer-Science/Page43846.html"],
}

bachelor_links_german = {
    "architektur": ["https://www.tha.de/Binaries/Binary_37263/Architektur-BA-MA-SPO-2019-C-Studienverlauf.pdf",
                    "Weitere Informationen hier: https://www.tha.de/Architektur-und-Bauwesen/Architektur-Bachelor.html"],

    ("betriebswirtschaft", "bwl"): [
        "https://www.tha.de/Binaries/Binary68290/Betriebswirtschaft-BW-Modulhandbuch-abWiSe2023-24.pdf",
        "Weitere Informationen hier: https://www.tha.de/Wirtschaft/Betriebswirtschaft-Bachelor.html"],

    "wirtschaftspsychologie": [
        "./backend/rasa/actions/images/business-psychology1.webp",
        "./backend/rasa/actions/images/business-psychology2.webp",
        "./backend/rasa/actions/images/business-psychology3.webp",
        "Weitere Informationen hier: https://www.tha.de/Wirtschaft/Wirtschaftspsychologie.html"],

    ("bauingenieurwesen", "bauingenieur"): [
        "https://www.tha.de/Binaries/Binary72332/Bauingenieurwesen.mp4",
        "Weitere Informationen hier: https://www.tha.de/Architektur-und-Bauwesen/bachelor-bau.html"],

    "kommunikationsdesign": [
        "./backend/rasa/actions/images/communication-design.webp",
        "Weitere Informationen hier: https://www.tha.de/Gestaltung/KD.html"],

    ("technische informatik", "ti", "technische it"): [
        "./backend/rasa/actions/images/computer-engineering.png",
        "Weitere Informationen hier: https://www.tha.de/Informatik/Technische-Informatik.html"],

    "informatik": [
        "./backend/rasa/actions/images/computer-science.webp",
        "Weitere Informationen hier: https://www.tha.de/Informatik/Informatik-Bachelor.html"],

    "creative engineering": [
        "./backend/rasa/actions/images/creative-engineering.webp",
        "Weitere Informationen hier: https://www.tha.de/Gestaltung/Creative-Engineering.html"],

    "data science": [
        "./backend/rasa/actions/images/data-science.webp",
        "Weitere Informationen hier: https://www.tha.de/Geistes-und-Naturwissenschaften/Data-Science.html"],

    "digitaler baumeister": [
        "./backend/rasa/actions/images/digital-design.webp",
        "Weitere Informationen hier: https://www.tha.de/Architektur-und-Bauwesen/Digitaler-Baumeister-Bachelor.html"],

    "elektrotechnik": [
        "https://www.tha.de/Binaries/Binary_13160/Studienplan-ElektrotechnikEA-IK.pdf",
        "Weitere Informationen hier: https://www.tha.de/Elektrotechnik/Elektrotechnik-Bachelor.html"],

    ("energieeffizientes planen und bauen", "energieeffizientes planen", "energieeffizientes bauen"): [
        "./backend/rasa/actions/images/energy-efficient-planning.jpg",
        "Weitere Informationen hier: https://www.tha.de/Architektur-und-Bauwesen/Energieeffizientes-Planen-und-Bauen-Bachelor.html"],

    ("umwelt und verfahrenstechnik", "umwelt technik", "umwelt verfahrenstechnik"): [
        "./backend/rasa/actions/images/environmental-process-engineering.webp",
        "Weitere Informationen hier: https://www.tha.de/fmv/umwelt-und-verfahrenstechnik-bachelor.html"],

    "industrial engineering": [
        "./backend/rasa/actions/images/industrial-engineering.webp",
        "Weitere Informationen hier: https://www.tha.de/Geistes-und-Naturwissenschaften/Wirtschaftsingenieurwesen-berufsbegleitend-fuer-Teilnehmer-innen-mit-betriebswirtschaftlichem-Abschluss.html"],

    "wirtschaftsinformatik": [
        "./backend/rasa/actions/images/information-systems.webp",
        "Weitere Informationen hier: https://www.tha.de/Informatik/Wirtschaftsinformatik-Bachelor.html"],

    ("interaktive medien", "medien"): [
        "./backend/rasa/actions/images/interaktive_medien.webp",
        "Weitere Informationen hier: https://www.tha.de/Gestaltung/Interaktive-Medien-Interaktive-Mediensysteme/IA.html"],

    ("international management", "internationales management", "internationale wirtschaftsinformatik",
     "internationales wirtschaftsingenieurwesen"): [
        "https://www.tha.de/Binaries/Binary29943/MHB-IM-SPO2016-WiSe21-22.pdf",
        "Weitere Informationen hier: https://www.tha.de/Informatik/International-Information-Systems-Internationale-Wirtschaftsinformatik.html"],

    "maschinenbau": [
        "./backend/rasa/actions/images/mechanical-engineering.webp",
        "Weitere Informationen hier: https://www.tha.de/fmv/maschinenbau-bachelor.html"],

    "mechatronik": [
        "https://www.tha.de/Binaries/Binary28103/Studienplan-Mechatronik-neu-korr.pdf",
        "Weitere Informationen hier: https://www.tha.de/Elektrotechnik/Mechatronik-Bachelor.html"],

    "soziale arbeit": [
        "./backend/rasa/actions/images/social-work.webp",
        "Weitere Informationen hier: https://www.tha.de/Geistes-und-Naturwissenschaften/Soziale-Arbeit.html"],

    "systems engineering": [
        "./backend/rasa/actions/images/systems-engineering.webp",
        "Weitere Informationen hier: https://www.tha.de/Informatik/Systems-Engineering-Bachelor.html"]

}

master_links_english = {
    "applied research": ["https://cloud.hs-augsburg.de/s/j84QCtf2pPmSqDC",
                         " More information here: https://www.tha.de/Elektrotechnik/Applied-Research-Master.html"],

    "architecture": ["./backend/rasa/actions/images/Architektur_Master.webp",
                     "More information here: https://www.tha.de/Architektur-und-Bauwesen/Architektur-Master.html"],

    "business information systems": ["./backend/rasa/actions/images/BIS_Master.png",
                                     "More information here: https://www.tha.de/en/Computer-Science/Business-Information-Systems-MSc.html"],

    "civil engineering": ["./backend/rasa/actions/images/Civil_Engineering_Master.png",
                          "More information here: https://www.tha.de/en/Architecture-and-Civil-Engineering/Civil-Engineering.html"],

    ("computer science", "cs", "informatic", "informatics"): [
        "./backend/rasa/actions/images/Computer_science_Master.webp",
        "More information here: https://www.tha.de/en/Computer-Science/Computer-Science-MSc.html"],

    "energy efficiency design": ["./backend/rasa/actions/images/E2D_Master.webp",
                                 "More information here: https://www.tha.de/en/Architecture-and-Civil-Engineering/Energy-Efficiency-Design-E2D.html"],

    ("environmental process engineering", "environmental engineering"): [
        "./backend/rasa/actions/images/Environmental_process_eng_Master_EN.webp",
        "More information here: https://www.tha.de/en/Mechanical-and-Process-Engineering/mmu-EN.html"],

    ("human resource management", "hr management", "human resource"): [
        "https://www.tha.de/Binaries/Binary_39450/Moduluebersicht-PMG2020-Stand-07042020.pdf",
        "More information here: https://www.tha.de/en/School-of-Business/Human-Resource-Management-MSc.html"],

    "identity design": ["./backend/rasa/actions/images/Identity_Design_Master.webp",
                        "More information here: https://www.tha.de/en/Design/Identity-Design.html"],

    "industrial safety and security": [
        "https://www.tha.de/Binaries/Binary_48021/Studienplan-Vollzeit-Master-Industrielle-Sicherheit.pdf",
        "https://www.tha.de/Binaries/Binary_71171/Studienplan-Teilzeit-Master-Industrielle-Sicherheit.pdf"
        "More information here: https://www.tha.de/en/Electrical-Engineering/Industrial-Safety-and-Security-MSc.html"],

    ("interactive media systems", "interactive media", "ims"): [
        "./backend/rasa/actions/images/interactive_media_systems_Master.webp",
        "More information here: https://www.tha.de/en/Design/Interactive-Media/Interactive-Media-Systems.html"],

    ("international business and finance", "international finance", "international business", "finance"): [
        "https://www.tha.de/Binaries/Binary_64862/Module-Description-IBF-Master-2022-v3.pdf",
        "More information here: https://www.tha.de/en/School-of-Business/International-Business-and-Finance-MA.html"],

    ("it project and process management", "it project management", "project process management"): [
        "./backend/rasa/actions/images/IT_Project_project_management_Master.webp",
        "More information here: https://www.tha.de/en/Computer-Science/IT-Project-and-Process-Management-2.html"],

    ("marketing management digital", "marketing management", "digital marketing"): [
        "./backend/rasa/actions/images/Marekting_Management_dig_Master.png",
        "More information here: https://www.tha.de/en/School-of-Business/Marketing-Management-Digital-Master.html"],

    ("mechanical engineering", "mechanics", "mechanic"): [
        "./backend/rasa/actions/images/Mechanical_engineering_Master.webp",
        "More information here: https://www.tha.de/en/Mechanical-and-Process-Engineering/Mechanical-Engineering-MEng.html"],

    ("mechatronic systems", "mechatronics"): [
        "https://www.tha.de/Binaries/Binary_28347/Studienplan-Master-Mech-Sys.pdf",
        " More information here: https://www.tha.de/en/Electrical-Engineering/Mechatronic-Systems-MEng.html"],

    ("production engineering", "production"): [
        "./backend/rasa/actions/images/Production_engineering_Master.webp",
        "More information here: https://www.tha.de/en/Mechanical-and-Process-Engineering/Production-Engineering.html"],

    ("project management civil engineering", "civil project management"): [
        "https://www.tha.de/Binaries/Binary33338/THA-Postkarte-Bau-WB-Master-PM-final.pdf",
        "More information here: https://www.tha.de/en/Architecture-and-Civil-Engineering/Institute-for-Construction-and-Real-Estate/Project-Management-Civil-Engineering-MEng.html"],

    "sustainability management": [
        "./backend/rasa/actions/images/sustainibility_management_Master.webp",
        "More information here: https://www.tha.de/en/School-of-Business/Sustainability-Management.html"],

    "taxation and accounting": ["https://www.tha.de/Binaries/Binary74026/U-bersicht-u-ber-den-Studiengang.pdf",
                                "More information here: https://www.tha.de/en/School-of-Business/Taxation-and-Accounting-MA.html"],

    "technology management": ["./backend/rasa/actions/images/Technology_management_Master.webp",
                              "More information here: https://www.tha.de/en/Mechanical-and-Process-Engineering/tm-EN.html"],

    "transformation design": ["./backend/rasa/actions/images/Transformation_design_Master.webp",
                              "More information here: https://www.tha.de/en/Design/Transformation-Design-2/Transformation-Design.html"],

}

master_links_german = {
    ("angewandte forschung in den ingenieurwissenschaften", "angewandte forschung"): [
        "https://cloud.hs-augsburg.de/s/j84QCtf2pPmSqDC",
        "Weitere Informationen hier: https://www.tha.de/Elektrotechnik/Applied-Research-Master.html"],

    "architektur": [
        "./backend/rasa/actions/images/Architektur_Master.webp",
        "Weitere Informationen hier: https://www.tha.de/Architektur-und-Bauwesen/Architektur-Master.html"],

    ("wirtschaftsinformationssysteme", "business information systems"): [
        "./backend/rasa/actions/images/BIS_Master.png",
        "Weitere Informationen hier: https://www.tha.de/Informatik/Business-Information-Systems.html"],

    ("bauingenieurwesen", "bauingenieur"): [
        "./backend/rasa/actions/images/Civil_Engineering_Master.png",
        "Weitere Informationen hier: https://www.tha.de/Architektur-und-Bauwesen/Bauingenieurwesen-Master.html"],

    "informatik": [
        "./backend/rasa/actions/images/Computer_science_Master.webp",
        "Weitere Informationen hier: https://www.tha.de/Informatik/Informatik-Master.html"],

    "energieeffizientes design": [
        "./backend/rasa/actions/images/E2D_Master.webp",
        "Weitere Informationen hier: https://www.tha.de/Architektur-und-Bauwesen/Energie-Effizienz-Design-Master.html"],

    ("umwelt und verfahrenstechnik", "umwelttechnik", "umwelt technik"): [
        "./backend/rasa/actions/images/Environmental_process_eng_Master_EN.webp",
        "Weitere Informationen hier: https://www.tha.de/fmv/umwelt-und-verfahrenstechnik-master.html"],

    ("human resource management", "hr", "hr management", "human resource", "personalmanagement"): [
        "https://www.tha.de/Binaries/Binary_39450/Moduluebersicht-PMG2020-Stand-07042020.pdf",
        "Weitere Informationen hier: https://www.tha.de/Wirtschaft/Personalmanagement-Master.html"],

    "identity design": [
        "./backend/rasa/actions/images/Identity_Design_Master.webp",
        "Weitere Informationen hier: https://www.tha.de/en/Design/Identity-Design.html"],

    "industrielle sicherheit": [
        "https://www.tha.de/Binaries/Binary_48021/Studienplan-Vollzeit-Master-Industrielle-Sicherheit.pdf",
        "https://www.tha.de/Binaries/Binary_71171/Studienplan-Teilzeit-Master-Industrielle-Sicherheit.pdf",
        "Weitere Informationen hier: https://www.tha.de/Elektrotechnik/Industrielle-Sicherheit-Master.html"],

    ("interaktive medien", "ims", "interaktive mediensysteme"): [
        "./backend/rasa/actions/images/interactive_media_systems_Master.webp",
        "Weitere Informationen hier: https://www.tha.de/Gestaltung/Interaktive-Medien/IMS.html"],

    ("international business und finance", "international business", "international finance", "finance"): [
        "https://www.tha.de/Binaries/Binary_64862/Module-Description-IBF-Master-2022-v3.pdf",
        "Weitere Informationen hier: https://www.tha.de/Wirtschaft/International-Business-and-Finance-Master.html"],

    ("it projektmanagement und prozessmanagement", "it projektmanagement", "project and process management",
     "it management"): [
        "./backend/rasa/actions/images/IT_Project_project_management_Master.webp",
        "Weitere Informationen hier: https://www.tha.de/Informatik/it-pm.html"],

    ("marketing management digital", "marketing management"): [
        "./backend/rasa/actions/images/Marekting_Management_dig_Master.png",
        "Weitere Informationen hier: https://www.tha.de/Wirtschaft/Marketing-Management-Digital-Master.html"],

    "maschinenbau": [
        "./backend/rasa/actions/images/Mechanical_engineering_Master.webp",
        "Weitere Informationen hier: https://www.tha.de/fmv/maschinenbau-master.html"],

    ("mechatronic systems", "mechatronik"): [
        "https://www.tha.de/Binaries/Binary_28347/Studienplan-Master-Mech-Sys.pdf",
        "Weitere Informationen hier: https://www.tha.de/Elektrotechnik/Mechatronic-Systems-Master.html"],

    ("production engineering", "produktion"): [
        "./backend/rasa/actions/images/Production_engineering_Master.webp",
        "Weitere Informationen hier: https://www.tha.de/fmv/produktion-master.html"],

    ("project management civil engineering", "civil project management", "projektmanagement bau"): [
        "./backend/rasa/actions/images/projektmanagement_bau.webp",
        "Weitere Informationen hier: https://www.tha.de/Architektur-und-Bauwesen/ibi/Master-Projektmanagement.html"],

    ("nachhaltigkeit management", "nachhaltigkeitsmanagement"): [
        "./backend/rasa/actions/images/sustainibility_management_Master.webp",
        "Weitere Informationen hier: https://www.tha.de/Wirtschaft/Nachhaltigkeitsmanagement-Master.html"],

    "steuern und rechnungslegung": [
        "https://www.tha.de/Binaries/Binary74026/U-bersicht-u-ber-den-Studiengang.pdf",
        "Weitere Informationen hier: https://www.tha.de/Wirtschaft/Steuern-und-Rechnungslegung-Master.html"],

    "technologie management": [
        "./backend/rasa/actions/images/Technology_management_Master.webp",
        "Weitere Informationen hier: https://www.tha.de/fmv/technologie-management-master.html"],

    "transformation design": [
        "./backend/rasa/actions/images/Transformation_design_Master.webp",
        "Weitere Informationen hier: https://www.tha.de/Gestaltung/Transformation-Design/Studieninhalt.html"]

}

bachelor_synonyms = ["bachelor", "bachelors", "bachelor's"]
master_synonyms = ["master", "masters", "master's"]

# Add known words to the dictionary
known_words = [
    "architecture", "business administration", "business psychology", "civil engineering",
    "communication design", "computer engineering", "computer science", "informatics",
    "creative engineering", "data science", "digital design and production", "digital design",
    "design and production", "electrical engineering", "energy efficient planning and building",
    "energy planning", "environmental process engineering", "environmental engineering",
    "industrial engineering", "information systems", "interactive media", "international information systems",
    "international management", "mechanical engineering", "mechatronics", "social work",
    "systems engineering", "applied research", "architecture", "business management",
    "human resource management", "identity design", "industrial safety and security",
    "international business and finance", "IT project and process management",
    "marketing management", "mechanical engineering", "production engineering",
    "project management", "sustainability management", "taxation and accounting",
    "technology management", "transformation design", "Betriebswirtschaft", "Wirtschaftspsychologie",
    "Bauingenieurwesen", "Kommunikationsdesign", "Technische Informatik", "Creative Engineering",
    "Elektrotechnik", "Umwelttechnik", "Wirtschaftsinformatik", "Maschinenbau",
    "Soziale Arbeit", "Wirtschaftsinformationssysteme", "Energieeffizientes Design",
    "Informatik", "Maschinenbau", "Mechatronik"
]

spell = SpellChecker()
spell.word_frequency.load_words(known_words)


def studiengang_contained(links, studiengang):
    for key in links.keys():
        if isinstance(key, tuple):
            for k in key:
                if studiengang in k:
                    return True
        elif studiengang in key:
            return True
    return False


def get_value_by_partial_key(d, partial_key):
    for key in d:
        if isinstance(key, tuple) and partial_key in key:
            return d[key]
        elif key == partial_key:
            return d[key]
    return None


class ProvideGeneralStudyplanEnglish(Action):
    def name(self) -> Text:
        return "provide_general_studyplan_english"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        studiengang = tracker.get_slot("studiengang")
        study_type = tracker.get_slot("study_type")

        # spelling correction
        if studiengang:
            studiengang_words = studiengang.split()
            corrected_studiengang_words = [spell.correction(word) or word for word in studiengang_words]
            studiengang = " ".join(corrected_studiengang_words)

        if study_type:
            study_type_words = study_type.split()
            corrected_study_type_words = [spell.correction(word) or word for word in study_type_words]
            study_type = " ".join(corrected_study_type_words)

        if studiengang is not None:
            if study_type is None and (studiengang_contained(bachelor_links_english, studiengang) or
                                       studiengang_contained(master_links_english, studiengang)):
                dispatcher.utter_message("Bachelor or master?")
            elif study_type is not None:
                if (studiengang_contained(bachelor_links_english, studiengang) and
                        not studiengang_contained(master_links_english, studiengang)):
                    study_type = "bachelor"
                elif (studiengang_contained(master_links_english, studiengang) and
                      not studiengang_contained(bachelor_links_english, studiengang)):
                    study_type = "masters"
                try:
                    website_link = None
                    if study_type in bachelor_synonyms:
                        website_link = get_value_by_partial_key(bachelor_links_english, str(studiengang).lower())
                    elif study_type in master_synonyms:
                        website_link = get_value_by_partial_key(master_links_english, str(studiengang).lower())

                    if website_link is None:
                        dispatcher.utter_message(text="Found no study plan. Is the course name correct?")
                        return [SlotSet("study_type", None), SlotSet("studiengang", None)]

                    else:
                        links_text = "\n".join(website_link)
                        dispatcher.utter_message(
                            f"Here is the study plan for {str(study_type)} {str(studiengang).title()}:\n{links_text}")
                        return [SlotSet("study_type", None), SlotSet("studiengang", None)]
                except Exception as _:
                    dispatcher.utter_message("An unknown error occurred, please try again.")
            else:
                dispatcher.utter_message(text="Found no study plan. Is the course name correct?")
                return [SlotSet("study_type", None), SlotSet("studiengang", None)]

        else:
            dispatcher.utter_message("What are you currently studying?")

        return []


class ProvideGeneralStudyplanGerman(Action):
    def name(self) -> Text:
        return "provide_general_studyplan_german"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        studiengang = tracker.get_slot("studiengang")
        study_type = tracker.get_slot("study_type")

        if studiengang:
            studiengang_words = studiengang.split()
            corrected_studiengang_words = [spell.correction(word) or word for word in studiengang_words]
            studiengang = " ".join(corrected_studiengang_words)

        if study_type:
            study_type_words = study_type.split()
            corrected_study_type_words = [spell.correction(word) or word for word in study_type_words]
            study_type = " ".join(corrected_study_type_words)

        if studiengang is not None:
            if study_type is None and (studiengang_contained(bachelor_links_german, studiengang) or
                                       studiengang_contained(master_links_german, studiengang)):
                dispatcher.utter_message("Bachelor oder Master?")
            elif study_type is not None:
                if (studiengang_contained(bachelor_links_german, studiengang) and
                        not studiengang_contained(master_links_german, studiengang)):
                    study_type = "bachelor"
                elif (studiengang_contained(master_links_german, studiengang) and
                      not studiengang_contained(bachelor_links_german, studiengang)):
                    study_type = "masters"
                try:
                    website_link = None
                    if study_type in bachelor_synonyms:
                        website_link = get_value_by_partial_key(bachelor_links_german, str(studiengang).lower())
                    elif study_type in master_synonyms:
                        website_link = get_value_by_partial_key(master_links_german, str(studiengang).lower())

                    if website_link is None:
                        dispatcher.utter_message(
                            text="Studienplan nicht gefunden. Ist der Name des Studiengangs korrekt?")
                        return [SlotSet("study_type", None), SlotSet("studiengang", None)]
                    else:
                        links_text = "\n".join(website_link)
                        dispatcher.utter_message(
                            f"Hier ist der Studienplan für {str(study_type)} {str(studiengang).title()}:\n{links_text} ")
                        return [SlotSet("study_type", None), SlotSet("studiengang", None)]
                except Exception as _:
                    dispatcher.utter_message("Ein unbekannter Fehler ist aufgetreten, bitte versuchen Sie es erneut.")
            else:
                dispatcher.utter_message(text="Studiengang nicht gefunden. Ist der Name des Studiengangs korrekt?")
                return [SlotSet("study_type", None), SlotSet("studiengang", None)]
        else:
            dispatcher.utter_message("Was studieren Sie derzeit?")

        return []


class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(
            text="Sorry, I cannot answer this question. Please find more information here: https://tha.de/")
        # German response
        dispatcher.utter_message(
            text="Entschuldigung, ich kann diese Frage nicht beantworten. Hier finden Sie Informationen über die "
                 "Hochschule: https://tha.de/")
        return []
