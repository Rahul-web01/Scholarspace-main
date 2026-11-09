#!/usr/bin/env python3
"""Build assets/js/catalog.js (every subject and its Drive files) for the ScholarSpace site.

How to refresh after you add files to Google Drive:
    python3 tools/crawl_drive.py 1KDEa-DkdkNl6FuhUDO9upWKTaSeQlRNC tools/drive-tree.tsv
    python3 tools/build_catalog.py

  * tools/drive-tree.tsv  path, kind (file/folder) and Drive ID of everything in the public Drive folder
  * tools/titles.tsv      optional clean display title for a file path (otherwise the file name is cleaned up)
  * SUBJECTS below        which Drive folders / files belong to which subject

A source ending in a file extension is one file, "id:<Drive file ID>" is one file found by its ID (keeps working
after the file is renamed on Drive), and anything else is a folder (everything under it).
Single files are assigned first, so a file can be pulled out of a folder that belongs to another subject.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
ROOT_FOLDER = "1KDEa-DkdkNl6FuhUDO9upWKTaSeQlRNC"
# BBA material lives in its own public Drive folder; its paths get the prefix "BBA/".
#   python3 tools/crawl_drive.py 1GhW9UVlo35eLvbHPEsSv4NiCul0hkml6 tools/bba-drive-tree.tsv
BBA_FOLDER = "1GhW9UVlo35eLvbHPEsSv4NiCul0hkml6"
TREES = [("drive-tree.tsv", ""), ("bba-drive-tree.tsv", "BBA/")]

# Never published on the site: paid books, a program, a saved web page, ads and junk.
EXCLUDE = re.compile(
    r"^apache-maven|^quantum/|Claude_files|askbooks|quantum|^Syllabus/DumpStack|"
    r"ESE/Very Important\.pdf$|\.(log|tmp)$|^(?!BBA/).*\.(jpg|jpeg|png)$|"
    # BBA: classmates' submitted work (names and roll numbers), a class score sheet, a paid book, non-study files
    r"^BBA/.*/Student Assignments/|^BBA/.*/EF Quiz\.xlsx$|RESEARCH_METHODOLOGY_C_R_KOTHARI|^BBA/To check/", re.I)

# Each college's material stays separate: different syllabus, notes and exam difficulty.
#   BBD University: loose files, "Sem 5", "6 Sem" and the BBDU sessional / semester papers.
#   ITM College (AKTU): the "NOTES" folders inside "1st Year" ... "4th Year", and "Btech/".
PROGRAMS = [
    {"id": "btech-cse", "name": "B.Tech CSE · BBD University", "short": "BBD University", "college": "BBD University",
     "icon": "fa-building-columns", "course": "btech-cse",
     "blurb": "Arranged by the BBD University 2026-27 syllabus, with BBDU sessional and semester papers and practice sets.",
     "years": True},
    {"id": "itm-cse", "name": "B.Tech CSE · ITM College", "short": "ITM College (AKTU)", "college": "ITM College (AKTU)",
     "icon": "fa-school", "course": "btech-cse",
     "blurb": "ITM College material on the AKTU syllabus: unit-wise notes, one-shot notes and AKTU solutions.",
     "years": True},
    {"id": "btech-other", "name": "B.Tech Other Branches", "short": "Mechanical, Electrical, Civil", "icon": "fa-gears",
     "college": "ITM College (AKTU)",
     "blurb": "Mechanical, Electrical, Electronics and Civil subjects from ITM College (AKTU syllabus)."},
    {"id": "bpharm", "name": "B.Pharm", "short": "Pharmacy", "icon": "fa-prescription-bottle-medical",
     "blurb": "Bachelor of Pharmacy study material."},
    {"id": "agriculture", "name": "B.Sc Agriculture", "short": "Agriculture", "icon": "fa-seedling",
     "blurb": "Study material for Agriculture students."},
    {"id": "bba", "name": "BBA · BBD University", "short": "BBA", "college": "BBD University", "icon": "fa-briefcase",
     "course": "bba", "years": True,
     "blurb": "Bachelor of Business Administration, arranged by the BBD University 2023-24 (NEP 2020) syllabus."},
    {"id": "syllabus", "name": "Syllabus", "short": "Official syllabus PDFs", "icon": "fa-file-lines",
     "blurb": "Course structures and syllabi for B.Tech, B.Pharm and B.Arch programmes."},
]

def S(id, name, program, src, code="", year=None, sem="", group="core", icon="fa-book", alias=""):
    return dict(id=id, name=name, program=program, src=src, code=code, year=year, sem=sem,
                group=group, icon=icon, alias=alias)

I = "itm-cse"  # ITM College (AKTU)
BB = "bba"  # BBA, BBD University
B = "btech-cse"  # BBD University
SUBJECTS = [
    # ================= BBD University · B.Tech CSE (2026-27 syllabus) =================
    # ---------------- 1st Year (Semester I + II) ----------------
    S("calculus", "Calculus", B, ["id:1xEM8YdbWzT9BDthjNb1-H6Ixn4xq-wRf",
      "id:1jfnetLyyVzDPfnAIdLFdDU3SiHP-Ag7v", "id:15Bnw5Sl5QDQytaWyc78BwwQEJ81HD_Ma",
      "id:1AjhoBL3XtP5IgZkSLk8fRuAHEctS2K8O", "id:1ra9iGDDIX5o1aUAyKG2gLa6gvufO-kJP",
      "1st Year/Divergence of a Vector Function.pdf"], "RBS5103", 1, "I", icon="fa-square-root-variable",
      alias="maths 1 mathematics matrices"),
    S("c-programming", "Computer Concepts & Programming in C", B, ["C language practise set.pdf",
      "1st Year/C_Complete_Notes.pdf", "1st Year/Scanned_20241226-1423.pdf", "1st Year/Scanned_20241226-1423 (1).pdf",
      "1st Year/Scanned_20241226-1423 (2).pdf"], "RCS5101", 1, "I", icon="fa-c", alias="pps c language"),
    S("discrete-maths", "Discrete Mathematics", B, ["Sem 5/DM 09", "DM Module 1.pdf", "DM( recurrence relation ).pdf",
      "Module 2 Discrete.pdf", "Prepositional Logic (1).pdf", "final 2023-24.pdf"], "RBS5203", 1, "II",
      icon="fa-diagram-project", alias="dm dstl discrete structures"),
    S("python", "Programming Concepts with Python", B, ["Python practice set.pdf",
      "id:1q6Eo3pXr2ekcjwSXZGINptULuQciKAAB"], "RCS5201", 1, "II", icon="fa-python"),
    S("physics", "Quantum Physics & Advanced Functional Materials", B, ["Physics practice set .pdf",
      "DOC-20231024-WA0012..pdf", "DOC-20231224-WA0000..pdf", "1st Year/physics 1.pdf", "sessional 2 2024-25.pdf"],
      "RBS5101", 1, "I / II", "group-a", icon="fa-atom", alias="engineering physics"),
    S("mechanics", "Engineering Mechanics & Mechatronics", B, ["Engineering Mechanics Full Notes-2.pdf",
      "Mechanics Practice set .pdf"], "RME5101", 1, "I / II", "group-a", icon="fa-gear"),
    S("electronics", "Basic Electronics Engineering", B, ["electronic practice set.pdf", "semester 2023-24.pdf",
      "1st Year/Basic Electronics engg paper.pdf", "1st Year/BEC Module 1 Notes.pdf", "1st Year/BEC Module 2 Notes.pdf",
      "1st Year/BEC2101.pdf", "1st Year/BEC2201 BBD.pdf", "1st Year/Image to PDF 20221011 19.08.25.pdf"], "REC5101", 1,
      "I / II", "group-a", icon="fa-microchip", alias="bec"),
    S("environment", "Environment & Ecological Sustainability", B, ["EVS practice set .pdf", "semester 2023-24 (1).pdf"],
      "RBSA5103", 1, "I / II", "group-a", icon="fa-leaf", alias="evs environmental studies"),
    S("electrical", "Electrical Engineering Concepts", B, ["Electrical practise set.pdf",
      "id:1x3EBbPN7hU9Yqrs4WbV3AO7hnYKZkc2a", "id:1wVge1E9KuPY6_KTw6Crn4rSVlQdd5Egr",
      "Scanned_20241226-1418.pdf"], "REE5101", 1, "I / II", "group-b", icon="fa-bolt",
      alias="bee basic electrical engineering"),
    S("chemistry", "Sustainable Chemical Sciences", B, ["Chemistry Notes Complete.pdf",
      "id:1UJVOzJD0N8bl-_b1s0GgwgA6-jcP5b69"], "RBS5102", 1, "I / II", "group-b", icon="fa-flask",
      alias="engineering chemistry"),
    S("communication", "Professional & Workplace Communication", B, ["English Practice set .pdf",
      "id:13-AFVFdf2dKkA6mEvJNOliqvfLR7UW-R", "id:1d8F1qFPXt6AOrhTeJrMbs1XvYmtrDSwM", "Scanned_20241226-1419.pdf"],
      "RHSA5101", 1, "I / II", "group-b", icon="fa-comments", alias="communicative english soft skills"),
    S("ai-basics", "Basics of Artificial Intelligence", B, ["AI practice .pdf",
      "id:1nr00ItvNGdewM8LjVIQZvDJKwiHEqPFq"], "RCS5102", 1, "I / II", "group-b", icon="fa-robot"),

    # ---------------- 2nd Year (Semester III + IV) ----------------
    S("linear-algebra", "Linear Algebra", B, [], "RBS5303", 2, "III", icon="fa-square-root-variable"),
    S("data-structures", "Data Structures using C", B, ["Binary Tree implementation.docx.pdf",
      "DSUC practice set .pdf", "DSUC(NCS4302)-Module-1.pdf", "Final 2021-22(1).pdf", "Final 2021-22.pdf",
      "Linked List - algorithms.pdf", "Module-2 Stack - Queue.pdf", "Module-3Notes-TreeBinaryTree.pdf",
      "Unit-2StackQueue.pdf", "unit_4_DSUC.pdf", "DocScanner 25 May 2026 6-17\u202fpm.pdf"], "RCS5305", 2, "III",
      icon="fa-sitemap", alias="dsuc dsa"),
    S("java", "Core & Advanced Java", B, ["JAVA practice set .pdf", "Module 1 (Hand written).pdf", "Module 1 .pdf",
      "Module 2 .pdf"], "RCS5306", 2, "III", icon="fa-java", alias="oops"),
    S("digital-logic", "Digital Logic Design", B, ["DLD 2022-23.pdf", "DLD 2023-24.pdf", "DLD practice set.pdf",
      "sessional 1 (2023-24).pdf", "sessional 1 2024-25.pdf", "sessional 2 (2024-25).pdf"], "RCS5307", 2, "III",
      icon="fa-microchip", alias="dld dsd digital electronics"),
    S("startup", "Startup & Innovation", B, [], "RCS5311", 2, "III", icon="fa-lightbulb",
      alias="entrepreneurship"),
    S("constitution", "Indian Constitution", B, ["Scanned_20241204-2214.pdf", "sessional 2.pdf"], "RMC5301", 2, "III",
      icon="fa-scale-balanced", alias="coi constitution of india"),
    S("psychology", "Work & Organisational Psychology / Sociology of Work", B, [], "RHS5301 / RHS5302", 2,
      "III / IV", icon="fa-people-group", alias="organisational behaviour"),
    S("probability", "Probability & Statistics", B, [], "RBS5403", 2, "IV", icon="fa-chart-simple",
      alias="maths 4 statistics"),
    S("coa", "Computer Organization & Architecture", B, ["unit 4.pdf"], "RAI5402", 2, "IV", icon="fa-memory",
      alias="coa"),
    S("dbms", "Database Management Systems", B, [], "RCS5401", 2, "IV", icon="fa-database", alias="dbms sql"),
    S("software-engineering", "Software Engineering", B, ["Sem 5/Module-2.pdf"], "RCS5402", 2, "IV",
      icon="fa-code-branch", alias="se sdlc"),
    S("os", "Operating Systems", B, ["1st Year/Lec-2.pdf", "1st Year/lec_1Notes.pdf"], "RCS5404", 2, "IV",
      icon="fa-desktop", alias="os"),
    S("complex-analysis", "Complex Analysis & Integral Transforms", B, ["CAIT -2023-24.pdf",
      "Scanned_20241204-2039.pdf", "DOC-20230809-WA0015..pdf"], "", 2, "", "more", icon="fa-square-root-variable",
      alias="cait"),

    # ---------------- 3rd Year (Semester V + VI) ----------------
    S("ai-economy", "AI Economy & Digital Innovation", B, [], "RHS5501", 3, "V", icon="fa-chart-line"),
    S("automata", "Automata Theory & Formal Languages", B, ["Sem 5/ATFL 29"], "RCS5501", 3, "V",
      icon="fa-diagram-project", alias="tafl atfl toc"),
    S("microprocessor", "Microprocessor & Intelligent Embedded System", B, ["Sem 5/MI 04"], "RCS5503", 3, "V",
      icon="fa-microchip", alias="mi 8085 8086"),
    S("computer-networks", "Computer Networks", B, ["Sem 5/CN 27"], "RCS5502", 3, "V", icon="fa-network-wired",
      alias="cn"),
    S("machine-learning", "Machine Learning using Python", B, [], "RCS5504", 3, "V", icon="fa-brain", alias="ml"),
    S("eikt", "Essence of Indian Knowledge Tradition", B, ["Sem 5/EIKT 25"], "RMC5501", 3, "V", icon="fa-om"),
    S("industrial-management", "Industrial Management", B, ["6 Sem/IM", "IM.pdf"], "RHS5601", 3, "VI",
      icon="fa-industry", alias="im"),
    S("daa", "Design & Analysis of Algorithms", B, ["6 Sem/DAA", "DAA notes.pdf", "DAA.pdf",
      "6 Sem/IOT/syllabus_DAA.pdf"], "RCS5603", 3, "VI", icon="fa-code", alias="daa algorithms"),
    S("compiler-design", "Compiler Design", B, ["6 Sem/CD", "Compiler Design Notes.pdf"], "RCS5604", 3, "VI",
      icon="fa-terminal", alias="cd"),
    S("deep-learning", "Deep Learning using Python", B, [], "RCS5605", 3, "VI", icon="fa-brain"),
    S("computer-graphics", "Computer Graphics", B, ["Sem 5/CG 08", "CG Unit 2.pdf", "Unit 3 CG Notes(By Shailja).pdf",
      "DOC-20250828-WA0000..pdf", "DOC-20250828-WA0001..pdf"], "", 3, "", "elective", icon="fa-shapes", alias="cg"),
    S("big-data", "Big Data", B, ["Big Data Unit- 2 coreconcept.pdf", "Big data unit-3 by Coreconcepts_ engineering.pdf"],
      "", 3, "", "elective", icon="fa-server", alias="hadoop"),
    S("spm", "Software Project Management", B, ["Spm unit-5 notes by Coreconcepts engineering.pdf"], "", 3, "",
      "elective", icon="fa-list-check"),
    S("economics", "Engineering & Managerial Economics", B, ["Sem 5/EME 02"], "", 3, "", "more",
      icon="fa-coins", alias="eme"),

    # ---------------- 4th Year (Semester VII + VIII) ----------------
    S("distributed-systems", "Distributed Systems", B, ["4th Year/Distributed system lab manual.docx.pdf",
      "4th Year/Distributed_System_Assignment_3.pdf"], "RCS5701", 4, "VII", icon="fa-circle-nodes"),
    S("cryptography", "Cryptography & Network Security", B, [], "RCS5702", 4, "VII", icon="fa-key"),
    S("ai-ethics", "AI Ethics", B, [], "RCS5703", 4, "VII", icon="fa-scale-balanced"),
    S("cyber-security", "Cyber Security & Computer Forensics", B, ["6 Sem/CL", "CLS.pdf"], "RCS5801", 4, "VIII",
      icon="fa-shield-halved", alias="cyber law"),
    S("iot", "Internet of Things", B, ["6 Sem/IOT", "1,Internet of things(santanu sasmal).pdf",
      "2,Communication protocols.pdf", "3,4IBM CLOUD and WATSON with REST API.pdf"], "", 4, "", "elective",
      icon="fa-wifi", alias="iot"),
    S("computer-vision", "Computer Vision", B, ["4th Year/COMPUTER_VISION_2025_ODD_Semester.pdf",
      "4th Year/COMPUTER_VISION_2026_EVEN_Semester.pdf", "4th Year/CV module 1st notes .pdf"], "", 4, "", "elective",
      icon="fa-eye", alias="cv"),
    S("disaster-management", "Disaster Management", B, ["4th Year/DM NOTES_1.pdf", "4th Year/DM UNIT 3.pdf",
      "4th Year/unit 4.1.pdf", "4th Year/unit 4.2.pdf"], "", 4, "", "more", icon="fa-house-crack"),

    # ================= ITM College (AKTU) · B.Tech CSE =================
    # ITM ids are "itm-" + the old id where one existed, so old links still find the subject.
    # ---------------- 1st Year ----------------
    S("itm-maths-1", "Engineering Mathematics I", I, ["1st Year/NOTES/MATHS 1"], "", 1, "I",
      icon="fa-square-root-variable", alias="maths 1 m1 calculus matrices"),
    S("itm-maths-2", "Engineering Mathematics II", I, ["1st Year/NOTES/M2"], "", 1, "II",
      icon="fa-square-root-variable", alias="m2 maths"),
    S("itm-physics", "Engineering Physics", I, ["1st Year/NOTES/PHYSICS NOTES"], "", 1, "I / II", icon="fa-atom"),
    S("itm-chemistry", "Engineering Chemistry", I, ["1st Year/NOTES/CHEMISTRY"], "", 1, "I / II", icon="fa-flask"),
    S("itm-electrical", "Basic Electrical Engineering", I, ["1st Year/NOTES/BEE"], "", 1, "I / II", icon="fa-bolt",
      alias="bee"),
    S("itm-electronics", "Basic Electronics Engineering", I, ["1st Year/NOTES/Electronic"], "", 1, "I / II",
      icon="fa-microchip", alias="bec"),
    S("itm-pps", "Programming for Problem Solving", I, ["1st Year/NOTES/PPS"], "", 1, "I / II", icon="fa-c",
      alias="pps c programming language"),
    S("itm-mechanics", "Engineering Mechanics", I, ["1st Year/NOTES/MECHANIC_S"], "", 1, "I / II", icon="fa-gear",
      alias="mechanical"),
    S("itm-environment", "Environment & Ecology", I, ["1st Year/NOTES/Environmental and Ecology"], "", 1, "I / II",
      icon="fa-leaf", alias="evs environmental studies"),
    S("itm-soft-skills", "Soft Skills", I, ["1st Year/NOTES/Soft skill"], "", 1, "I / II", icon="fa-comments",
      alias="english communication"),
    # ---------------- 2nd Year ----------------
    S("itm-data-structures", "Data Structures", I, ["2nd Year/NOTES/Data structures notes"], "", 2, "",
      icon="fa-sitemap", alias="dsa ds"),
    S("itm-coa", "Computer Organization & Architecture", I, ["2nd Year/NOTES/COA NOTES"], "", 2, "",
      icon="fa-memory", alias="coa"),
    S("itm-digital-electronics", "Digital Electronics & System Design", I, ["2nd Year/NOTES/Digital system design (DSD)",
      "Btech/2nd Year/NOTES/Digital system design (DSD)", "2nd Year/NOTES/Electronic"], "", 2, "",
      icon="fa-microchip", alias="dsd de dld digital logic"),
    S("itm-maths-4", "Engineering Mathematics IV", I, ["2nd Year/NOTES/M4", "Btech/2nd Year/NOTES/M4"], "", 2, "",
      icon="fa-chart-simple", alias="m4 maths 4 probability statistics"),
    S("itm-python", "Python Programming", I, ["2nd Year/NOTES/Python notes"], "", 2, "", icon="fa-python"),
    S("itm-java", "Object Oriented Programming with Java", I, ["2nd Year/NOTES/Java"], "", 2, "", icon="fa-java",
      alias="java oops"),
    S("itm-os", "Operating Systems", I, ["2nd Year/NOTES/OS NOTES"], "", 2, "", icon="fa-desktop", alias="os"),
    S("itm-automata", "Theory of Automata & Formal Languages", I, ["2nd Year/NOTES/TAFL Notes"], "", 2, "",
      icon="fa-diagram-project", alias="tafl toc automata"),
    S("itm-cyber-security", "Cyber Security", I, ["2nd Year/NOTES/Cyber security"], "", 2, "",
      icon="fa-shield-halved"),
    S("itm-software-engineering", "Software Engineering", I, ["2nd Year/NOTES/Software Engineering"], "", 2, "",
      icon="fa-code-branch", alias="se sdlc"),
    S("itm-microprocessor", "Microprocessor", I, ["2nd Year/NOTES/MICROPROCESSOR NOTES"], "", 2, "",
      icon="fa-microchip", alias="mp 8085 8086"),
    S("itm-uhv", "Universal Human Values", I, ["2nd Year/NOTES/UHV"], "", 2, "", "open",
      icon="fa-hand-holding-heart", alias="uhv"),
    S("itm-technical-communication", "Technical Communication", I, ["2nd Year/NOTES/TC"], "", 2, "", "open",
      icon="fa-pen-nib", alias="tc"),
    S("itm-energy-science", "Energy Science & Engineering", I, ["2nd Year/NOTES/ESE"], "", 2, "", "open",
      icon="fa-bolt", alias="ese"),
    # ---------------- 3rd Year ----------------
    S("itm-dbms", "Database Management Systems", I, ["3rd year/NOTES/DBMS", "Btech/3rd year/NOTES/DBMS"], "", 3, "",
      icon="fa-database", alias="dbms sql"),
    S("itm-daa", "Design & Analysis of Algorithms", I, ["3rd year/NOTES/DAA", "Btech/3rd year/NOTES/DAA",
      "4th Year/Notes/AI/MA/UNIT-02-DAA-By-Multiatoms (1).pdf"], "", 3, "", icon="fa-code", alias="daa algorithms"),
    S("itm-computer-networks", "Computer Networks", I, ["3rd year/NOTES/COMPUTER NETWORKS",
      "Btech/3rd year/NOTES/COMPUTER NETWORKS"], "", 3, "", icon="fa-network-wired", alias="cn"),
    S("itm-compiler-design", "Compiler Design", I, ["3rd year/NOTES/COMPILER DESIGN NOTES"], "", 3, "",
      icon="fa-terminal", alias="cd"),
    S("itm-web-technology", "Web Technology", I, ["3rd year/NOTES/Web Technology", "3rd year/NOTES/Web Designing"], "",
      3, "", icon="fa-globe", alias="html css javascript web designing"),
    S("itm-machine-learning", "Machine Learning Techniques", I, ["3rd year/NOTES/ML", "3rd year/NOTES/MLT"], "", 3, "",
      "elective", icon="fa-brain", alias="ml mlt"),
    S("itm-deep-learning", "Deep Learning", I, ["3rd year/NOTES/Deep learning"], "", 3, "", "elective",
      icon="fa-brain"),
    S("itm-big-data", "Big Data", I, ["3rd year/NOTES/Big Data"], "", 3, "", "elective", icon="fa-server",
      alias="hadoop"),
    S("itm-data-analytics", "Data Analytics", I, ["3rd year/NOTES/Data Analytics Notes"], "", 3, "", "elective",
      icon="fa-chart-pie"),
    S("itm-data-mining", "Data Warehousing & Data Mining", I, ["3rd year/NOTES/Dwdm"], "", 3, "", "elective",
      icon="fa-cubes", alias="dwdm"),
    S("itm-data-compression", "Data Compression", I, ["3rd year/NOTES/Data Compression"], "", 3, "", "elective",
      icon="fa-file-zipper"),
    S("itm-soft-computing", "Application of Soft Computing", I, ["3rd year/NOTES/Application of soft computing"], "",
      3, "", "elective", icon="fa-circle-nodes"),
    S("itm-oosd", "Object Oriented System Design", I, ["3rd year/NOTES/OOSD", "Btech/3rd year/NOTES/OOSD"], "", 3, "",
      "elective", icon="fa-object-group", alias="oosd uml"),
    S("itm-hci", "Human Computer Interface", I, ["3rd year/NOTES/Human Computer Interface"], "", 3, "", "elective",
      icon="fa-hand-pointer", alias="hci"),
    S("itm-spm", "Software Project Management", I, ["3rd year/NOTES/SPM notes"], "", 3, "", "elective",
      icon="fa-list-check", alias="spm"),
    S("itm-constitution", "Constitution of India", I, ["3rd year/NOTES/COI", "Btech/3rd year/NOTES/COI"], "", 3, "",
      "open", icon="fa-scale-balanced", alias="coi indian constitution"),
    S("itm-social-media-marketing", "Digital & Social Media Marketing", I, ["3rd year/NOTES/DSMM"], "", 3, "", "open",
      icon="fa-hashtag", alias="dsmm"),
    S("itm-buddha-jain", "Human Values in Buddha & Jain Darshan", I,
      ["3rd year/NOTES/Human value in buddha and jain darshan"], "", 3, "", "open", icon="fa-dharmachakra"),
    S("itm-itcs", "Indian Traditions, Culture & Society", I, ["3rd year/NOTES/ITCS"], "", 3, "", "open",
      icon="fa-landmark", alias="itcs"),
    # ---------------- 4th Year ----------------
    S("itm-artificial-intelligence", "Artificial Intelligence", I, ["4th Year/Notes/AI",
      "3rd year/NOTES/Artificial Intelligence"], "", 4, "", "elective", icon="fa-robot", alias="ai"),
    S("itm-cloud-computing", "Cloud Computing", I, ["4th Year/Notes/Cloud computing"], "", 4, "", "elective",
      icon="fa-cloud"),
    S("itm-blockchain", "Blockchain", I, ["4th Year/Notes/Blockchain"], "", 4, "", "elective", icon="fa-link"),
    S("itm-distributed-systems", "Distributed Systems", I, ["4th Year/Notes/Distributed Systems"], "", 4, "",
      "elective", icon="fa-circle-nodes"),
    S("itm-iot", "Internet of Things", I, ["4th Year/Notes/Iot"], "", 4, "", "elective", icon="fa-wifi", alias="iot"),
    S("itm-mobile-computing", "Mobile Computing", I, ["4th Year/Notes/Mobile Computing notes"], "", 4, "", "elective",
      icon="fa-mobile-screen"),
    S("itm-software-testing", "Software Testing", I, ["4th Year/Notes/Software Testing"], "", 4, "", "elective",
      icon="fa-bug"),
    S("itm-image-processing", "Digital Image Processing", I, ["4th Year/Notes/Digital Image processing"], "", 4, "",
      "elective", icon="fa-image", alias="dip"),
    S("itm-real-time-systems", "Real Time Systems", I, ["4th Year/Notes/Real time system RTS"], "", 4, "", "elective",
      icon="fa-stopwatch", alias="rts"),
    S("itm-startup", "Idea to Business Model", I, ["4th Year/Notes/IBM"], "", 4, "", "open", icon="fa-lightbulb",
      alias="ibm startup entrepreneurship"),
    S("itm-project-management", "Project Management & Entrepreneurship", I,
      ["4th Year/Notes/Project Management and Entrepreneurship"], "", 4, "", "open", icon="fa-diagram-successor",
      alias="pme"),
    S("itm-quality-management", "Quality Management", I, ["4th Year/Notes/Quality Management"], "", 4, "", "open",
      icon="fa-award"),
    S("itm-rural-development", "Rural Development", I, ["4th Year/Notes/Rural Development notes"], "", 4, "", "open",
      icon="fa-tractor"),
    S("itm-humane-society", "Vision for Humane Society", I, ["4th Year/Notes/Vision For Human Society"], "", 4, "",
      "open", icon="fa-people-roof"),

    # ================= ITM College (AKTU) · other B.Tech branches =================
    S("thermodynamics", "Thermodynamics", "btech-other", ["2nd Year/NOTES/Thermodynamics"], group="Mechanical",
      icon="fa-temperature-half"),
    S("fluid-mechanics", "Fluid Mechanics", "btech-other", ["2nd Year/NOTES/Fluid Mechanic_"], group="Mechanical",
      icon="fa-water"),
    S("heat-mass-transfer", "Heat & Mass Transfer", "btech-other", ["2nd Year/NOTES/Hmt", "3rd year/NOTES/HMT",
      "3rd year/NOTES/Heat Transfer"], group="Mechanical", icon="fa-fire", alias="hmt"),
    S("material-science", "Material Science", "btech-other", ["2nd Year/NOTES/Material Science"], group="Mechanical",
      icon="fa-cubes"),
    S("machine-design", "Machine Design", "btech-other", ["3rd year/NOTES/Machine Design"], group="Mechanical",
      icon="fa-gears"),
    S("ic-engine", "IC Engines", "btech-other", ["3rd year/NOTES/IC Engine"], group="Mechanical", icon="fa-car"),
    S("theory-of-machines", "Theory of Machines", "btech-other", ["3rd year/NOTES/Theory of Machine (TOM)"],
      group="Mechanical", icon="fa-gear", alias="tom"),
    S("industrial-engineering", "Industrial Engineering", "btech-other", ["3rd year/NOTES/INDUSTRIAL ENGINEERING"],
      group="Mechanical", icon="fa-industry"),
    S("power-plant", "Power Plant Engineering", "btech-other", ["4th Year/Notes/POWER PLANT ENGINEER"],
      group="Mechanical", icon="fa-industry"),
    S("network-theory", "Network Theory", "btech-other", ["2nd Year/NOTES/Network theory"], group="Electrical",
      icon="fa-bolt"),
    S("power-system", "Power Systems", "btech-other", ["3rd year/NOTES/Power System"], group="Electrical",
      icon="fa-plug"),
    S("switchgear", "Switchgear & Protection", "btech-other", ["3rd year/NOTES/Switch gear"], group="Electrical",
      icon="fa-toggle-on"),
    S("power-system-operation", "Power System Operation & Control", "btech-other",
      ["4th Year/Notes/Power system operation"], group="Electrical", icon="fa-tower-broadcast"),
    S("renewable-energy", "Renewable Energy Sources", "btech-other", ["4th Year/Notes/Renewable energy sources"],
      group="Electrical", icon="fa-solar-panel"),
    S("dsp", "Digital Signal Processing", "btech-other", ["3rd year/NOTES/Digital Signal Processing"],
      group="Electronics", icon="fa-wave-square", alias="dsp"),
    S("laser-systems", "Laser Systems & Applications", "btech-other",
      ["2nd Year/NOTES/Laser System and it_s applications"], group="Electronics", icon="fa-wand-magic-sparkles"),
    S("surveying", "Surveying & Geomatics", "btech-other", ["2nd Year/NOTES/Surveying and Geomatics"], group="Civil",
      icon="fa-compass-drafting"),

    # ---------------- Other programmes ----------------
    S("pharmaceutical-analysis", "Pharmaceutical Analysis", "bpharm", ["Bpharma/1st Year/Pharmaceutical analysis"],
      year=1, sem="I", icon="fa-vial"),
    S("biochemistry", "Biochemistry", "agriculture", ["Agriculture"], icon="fa-dna"),

    # ================= BBA · BBD University (2023-24 NEP syllabus) =================
    # core = DSC, elective = DSE / GE, skill = vocational (VC) and co-curricular (CC) courses
    S("bba-accounting", "Fundamentals of Accounting", BB, [], "NBBA5101", 1, "I", "core", icon="fa-calculator", alias="accounts accountancy"),
    S("bba-business-environment", "Business Environment", BB, ["BBA/BBA 1 Year/Business Environment (NBBA5102)"], "NBBA5102", 1, "I", "core", icon="fa-earth-asia", alias="be fiscal monetary policy mrtp"),
    S("bba-quantitative", "Quantitative Analysis for Management", BB, [], "NBBA5103", 1, "I", "core", icon="fa-chart-simple", alias="statistics qam"),
    S("bba-managing-diversity", "Managing Organizational Diversity", BB, ["BBA/BBA 1 Year/Managing Organizational Diversity (NSMVC5101)"], "NSMVC5101", 1, "I", "skill", icon="fa-people-group", alias="diversity"),
    S("bba-obpom", "Organization Behaviour & Principles of Management", BB, ["BBA/BBA 1 Year/Organization Behaviour and Principles of Management (NBBA5201)"], "NBBA5201", 1, "II", "core", icon="fa-sitemap", alias="ob pom obpom organisational behaviour"),
    S("bba-business-maths", "Business Mathematics", BB, [], "NBBA5202", 1, "II", "core", icon="fa-square-root-variable", alias="maths"),
    S("bba-business-organisation", "Business Organisation", BB, ["BBA/BBA 1 Year/Business Organisation (NBBA5203)"], "NBBA5203", 1, "II", "core", icon="fa-building", alias="bo business organization"),
    S("bba-advertising", "Advertising & Personal Selling", BB, ["BBA/BBA 1 Year/Advertising and Personal Selling (NGE5704)"], "NGE5704", 1, "II", "elective", icon="fa-bullhorn", alias="aps advertising sales promotion"),
    S("bba-logistics", "Logistics Management", BB, [], "NSMVC5201", 1, "II", "skill", icon="fa-truck", alias="logistics"),
    S("bba-pom", "Production & Operations Management", BB, [], "NBBA5301", 2, "III", "core", icon="fa-industry", alias="pom production operations"),
    S("bba-managerial-economics", "Managerial Economics", BB, ["BBA/BBA 2 Year/Managerial Economics (NBBA5302)"], "NBBA5302", 2, "III", "core", icon="fa-coins", alias="me economics pricing"),
    S("bba-marketing-management", "Marketing Management", BB, ["BBA/BBA 2 Year/Marketing Management (NBBA5303)"], "NBBA5303", 2, "III", "core", icon="fa-store", alias="mm marketing channels"),
    S("bba-nvpd", "New Venture Planning & Development", BB, ["BBA/BBA 2 Year/New Venture Planning and Development (NGE5706)"], "NGE5706", 2, "III", "elective", icon="fa-rocket", alias="nvpd startup venture capital"),
    S("bba-financial-literacy", "Financial Literacy", BB, ["BBA/BBA 2 Year/Financial Literacy (NSMCC5301)"], "NSMCC5301", 2, "III", "skill", icon="fa-piggy-bank", alias="finance"),
    S("bba-design-thinking", "Creativity & Design Thinking", BB, ["BBA/BBA 2 Year/Creativity and Design Thinking (NSMVC5301)"], "NSMVC5301", 2, "III", "skill", icon="fa-lightbulb", alias="design thinking creativity"),
    S("bba-cost-accounting", "Cost & Management Accounting", BB, [], "NBBA5401", 2, "IV", "core", icon="fa-file-invoice-dollar", alias="cma cost accounting"),
    S("bba-hrmd", "Human Resource Management & Development", BB, ["BBA/BBA 2 Year/Human Resource Management and Development (NBBA5402)"], "NBBA5402", 2, "IV", "core", icon="fa-user-tie", alias="hrm hrd hrmd"),
    S("bba-business-law", "Business Law", BB, [], "NBBA5403", 2, "IV", "core", icon="fa-scale-balanced", alias="law"),
    S("bba-investment-management", "Investment Management", BB, ["BBA/BBA 2 Year/Investment Management (NGE5708)"], "NGE5708", 2, "IV", "elective", icon="fa-arrow-trend-up", alias="im investment"),
    S("bba-lpd", "Leadership & Personality Development", BB, ["BBA/BBA 2 Year/Leadership and Personality Development (NSMCC5401)"], "NSMCC5401", 2, "IV", "skill", icon="fa-user-graduate", alias="lpd leadership personality communication"),
    S("bba-digital-marketing", "Digital Marketing", BB, ["BBA/BBA 2 Year/Digital Marketing (NSMVC5402)"], "NSMVC5402", 2, "IV", "skill", icon="fa-hashtag", alias="dm seo sem social media"),
    S("bba-bps", "Business Policy & Strategy", BB, ["BBA/BBA 3 Year/Business Policy and Strategy (NBBA5501)"], "NBBA5501", 3, "V", "core", icon="fa-chess", alias="bps strategy"),
    S("bba-project-management", "Project Management", BB, ["BBA/BBA 3 Year/Project Management (NBBA5502)"], "NBBA5502", 3, "V", "core", icon="fa-list-check", alias="pm"),
    S("bba-financial-management", "Financial Management", BB, ["BBA/BBA 3 Year/Financial Management (NBBA5503)"], "NBBA5503", 3, "V", "core", icon="fa-sack-dollar", alias="fm finance"),
    S("bba-consumer-behaviour", "Consumer Behaviour", BB, ["BBA/BBA 3 Year/Consumer Behaviour (NDSE57102)"], "NDSE57102", 3, "V", "elective", icon="fa-cart-shopping", alias="cb"),
    S("bba-financial-services", "Financial Services", BB, ["BBA/BBA 3 Year/Financial Services (NGE5710)"], "NGE5710", 3, "V", "elective", icon="fa-building-columns", alias="fs"),
    S("bba-entrepreneurial-finance", "Entrepreneurial Finance", BB, ["BBA/BBA 3 Year/Entrepreneurial Finance (NSMVC5501)"], "NSMVC5501", 3, "V", "skill", icon="fa-hand-holding-dollar", alias="ef financial statements"),
    S("bba-ibm", "International Business Management", BB, ["BBA/BBA 3 Year/International Business Management (NBBA5601)"], "NBBA5601", 3, "VI", "core", icon="fa-globe", alias="ibm international business"),
    S("bba-esbm", "Entrepreneurship & Small Business Management", BB, ["BBA/BBA 3 Year/Entrepreneurship and Small Business Management (NBBA5602)"], "NBBA5602", 3, "VI", "core", icon="fa-shop", alias="esbm msme sidbi dic"),
    S("bba-rural-management", "Rural Management", BB, ["BBA/BBA 3 Year/Rural Management (NBBA5603)"], "NBBA5603", 3, "VI", "core", icon="fa-tractor", alias="rural"),
    S("bba-research-methodology", "Research Methodology", BB, ["BBA/BBA 3 Year/Research Methodology (NDSE57104)"], "NDSE57104", 3, "VI", "elective", icon="fa-magnifying-glass-chart", alias="rm research"),
    S("bba-banking-insurance", "Banking & Insurance", BB, [], "NBBA5701", 4, "VII", "core", icon="fa-landmark", alias="banking insurance"),
    S("bba-brand-management", "Brand Management", BB, [], "NBBA5801", 4, "VIII", "core", icon="fa-tag", alias="brand"),

    S("syllabus", "Syllabus PDFs", "syllabus", ["Syllabus", "BBA/BBA Syllabus 2023-24 onwards (NEP 2020).pdf"],
      icon="fa-file-lines"),
]

EXT = re.compile(r"\.(pdf|docx?|pptx?|xlsx?|txt|jpe?g|png)$", re.I)
TYPES = [  # (type, pattern on "title + path"), first match wins
    ("syllabus", r"syllabus|course structure|evaluation scheme|regulations"),
    ("papers", r"question paper|sessional|semester|\bpyq\b|exam paper|\bpaper\b|final 20"),
    ("practice", r"practi[cs]e|\bdpp\b|assignment|important (questions|topics)|solutions?\b"),
    ("books", r"\bbook\b|slides|lecture slides|\bppt"),
]
STOP = {"and", "of", "the", "in", "using", "with", "to", "for", "&", "-", "i", "ii", "iv", "engineering", "advanced",
        "basic", "basics", "concepts", "design"}


def clean_name(path):
    t = EXT.sub("", os.path.basename(path))
    t = re.sub(r"DOC-\d{8}-WA\d+\.?|Scanned_\d{8}-\d{4}|DocScanner.*|CamScanner.*", "", t)
    t = re.sub(r"[_]+", " ", t)
    t = re.sub(r"\((?:\d+)\)", "", t)
    t = re.sub(r"\s+", " ", t).strip(" .-,")
    return t[:1].upper() + t[1:] if t else "Document"


def words(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 2}


def main():
    tree = []
    for name, prefix in TREES:
        for l in open(os.path.join(HERE, name)):
            if l.strip():
                p, k, i = l.rstrip("\n").split("\t")
                tree.append([(prefix + p).rstrip("/"), k, i])
    files = {p: i for p, k, i in tree if k == "file" and not EXCLUDE.search(p)}
    hidden = [p for p, k, i in tree if k == "file" and EXCLUDE.search(p)]
    folders = {p: i for p, k, i in tree if k == "folder"}
    titles = {}
    tpath = os.path.join(HERE, "titles.tsv")
    if os.path.exists(tpath):
        for line in open(tpath):
            p, _, t = line.rstrip("\n").partition("\t")
            if p != "path":
                titles[p] = t

    by_id = {i: p for p, i in files.items()}
    for s in SUBJECTS:  # resolve "id:..." sources to the file's current path
        s["src"] = [by_id.get(x[3:], x) if x.startswith("id:") else x for x in s["src"]]
    owner, problems = {}, []
    for s in SUBJECTS:  # single files first
        for src in s["src"]:
            if src.startswith("id:"):
                problems.append(f"{s['id']}: file ID not on Drive: {src}")
            elif EXT.search(src):
                if src not in files:
                    problems.append(f"{s['id']}: file not on Drive: {src}")
                elif src in owner:
                    problems.append(f"{s['id']}: file already in {owner[src]}: {src}")
                else:
                    owner[src] = s["id"]
    for s in SUBJECTS:  # then folders
        for src in s["src"]:
            if not EXT.search(src):
                if src.startswith("id:"):
                    continue
                if src not in folders:
                    problems.append(f"{s['id']}: folder not on Drive: {src}")
                for p in files:
                    if p.startswith(src + "/") and p not in owner:
                        owner[p] = s["id"]

    out_subjects = []
    for s in SUBJECTS:
        subj_words = words(s["name"] + " " + s["alias"])
        items = []
        for p, sid in owner.items():
            if sid != s["id"]:
                continue
            title = titles.get(p) or titles.get("id:" + files[p]) or clean_name(p)
            parts = [x.strip() for x in title.split(" - ")]
            if len(parts) > 1 and words(parts[0]) & subj_words:
                parts = parts[1:]
            kept = [x for x in parts if x.lower() not in ("notes", "question paper", "assignment")]
            if kept and re.search(r"[A-Za-z]", " ".join(kept)):
                parts = kept  # the page already groups files by type
            short = " - ".join(parts)
            hay = (title + " " + p).lower()
            kind = next((k for k, rx in TYPES if re.search(rx, hay)), "notes")
            ext = (EXT.search(p).group(1).lower() if EXT.search(p) else "file")
            items.append({"t": short, "k": kind, "id": files[p], "x": ext})
        items.sort(key=lambda it: [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", it["t"])])
        # no "open in Drive" button for a folder that holds files kept off the site
        drive = [folders[f] for f in s["src"] if not EXT.search(f) and f in folders
                 and not any(h.startswith(f + "/") for h in hidden)]
        out_subjects.append({k: v for k, v in {
            "id": s["id"], "name": s["name"], "program": s["program"], "code": s["code"], "year": s["year"],
            "sem": s["sem"], "group": s["group"], "icon": s["icon"], "alias": s["alias"], "folders": drive,
            "files": items}.items() if v not in ("", None, [])})

    unassigned = sorted(p for p in files if p not in owner)
    data = {"root": ROOT_FOLDER, "programs": PROGRAMS, "subjects": out_subjects}
    os.makedirs(os.path.join(SITE, "assets", "js"), exist_ok=True)
    with open(os.path.join(SITE, "assets", "js", "catalog.js"), "w") as f:
        f.write("/* Generated by tools/build_catalog.py from the public Google Drive folder. Do not edit by hand. */\n")
        f.write("window.CATALOG = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")

    n_files = sum(len(s.get("files", [])) for s in out_subjects)
    print(f"subjects {len(out_subjects)}, files linked {n_files}, published files on Drive {len(files)}")
    for p in problems:
        print("PROBLEM:", p)
    for p in unassigned:
        print("NOT LINKED:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
