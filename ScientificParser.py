import re
import os
import sys
from PyPDF2 import PdfReader


def transformAccent(line):
    """
    
    """
    accents = {
        "`": {
            "a": "à",
            "e": "è",
            "i": "ì",
            "o": "ò",
            "u": "ù"
        },
        "´": {
            "e": "é"
        },
        "¨": {
            "a": "ä",
            "e": "ë",
            "i": "ï",
            "o": "ö",
            "u": "ü",
            "y": "ÿ"
        },
        "^": {
            "a": "â",
            "e": "ê",
            "i": "î",
            "o": "ô",
            "u": "û"
        }
    }
    for ac in accents:
        for letter in accents[ac]:
            line = line.replace(" "+ ac + letter, accents[ac][letter])
    return line

def getTitle(metadata,text):
    title = None
    circlecopyrt = re.compile(r'.*circlecopyrt.*')
    if "/Title" in metadata and metadata["/Title"] != None and metadata["/Title"].rstrip() != "" and metadata["/Title"].count("/") <=2 and not circlecopyrt.search(metadata["/Title"]):
        title = metadata["/Title"]
    else:
        ss = text.split("\n")
        regexp = re.compile(r'((.*pages.*)|(.*[12][0-9]{3}$.*)|(.*©.*)|(.*circlecopyrt.*))')
        i = 0
        cancel = False
        while(regexp.search(ss[i])):
            #TODO On regarde si la ligne qu'on va sauter ne contient pas un mot contenant deux Majuscule
            #Ce qui est le cas quand la phrase de fin de fichier est suivi du titre sans qu'un retour
            # à la ligne n'est été inséré
            titleimbrique = re.compile(r'[A-Z]\w{3,}([A-Z].*)') # Regex qui prend dans une phrase un mot qui contient 2 maj qui sont séparé par minimum 3 minuscules
            rs = re.search(titleimbrique, ss[i])
            if(rs):
                title = rs.groups(1)[0]
                cancel = True                
                break
            i += 1
        if (not cancel):
            title = ss[i]
            startWithMinuscule = re.compile(r'(^[a-z]{1,}.*)')
            i += 1
            while(startWithMinuscule.match(ss[i])):
                title += " " + ss[i]
                i += 1
            #Le mot qui suit le titre peut aussi comporter une Majuscule et c'est en majorité le cas
            #Cependant ces mots sont séparé souvent par des mots de liaisons 
            #Donc si nous en avons en fin de ligne, alors cela veut dire que la ligne suivante fait partie du titre
            haveLisaisonWord = re.compile(r'.*(in|for|of|as|with|into|to|from)$')
            while(haveLisaisonWord.match(title)):
                title += " " + ss[i]
                i += 1
    
    return title

def getBiblio(metadata,text):
    biblio=""

    return biblio


def getAdresses(pdf):

    text = pdf.pages[0].extract_text()
    emails = re.findall("([a-zA-Z0-9_.+\-[),]+\s?@[a-zA-Z0-9-]+\.[a-z-.]+)", text)

    for i in range(len(emails)):
        if(re.findall("([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+", emails[i])): ""
        else: #split les emails factorisé avec des virgules et remettre le @
            ungroupEmails = emails[i].split(",")
            arrobase = re.findall("@[a-zA-Z0-9-]+\.[a-z-.]+", ungroupEmails[len(ungroupEmails)-1])
            ungroupEmails[len(ungroupEmails)-1] = re.sub("[),]+\s@[a-zA-Z0-9-]+\.[a-z-.]+","",ungroupEmails[len(ungroupEmails)-1])
            for j in range(len(ungroupEmails)):
                ungroupEmails[j] += arrobase[0]
                emails = ungroupEmails

    return emails

def getAuthors(metadata,text):
    """
    Extracts the authors and their emails from the PDF
    The authors are extracted from the metadata or with multiple regex if the metadata are not filled in
    """
    if(metadata.author!="" and metadata.author!=None):
        authors = metadata.author
    else:
        # Use regular expressions to extract the author
        authors_regex = re.compile(r"Author\(s\):\s*(.*)")
        authors_match = re.search(authors_regex, text)
        authors = authors_match.group(1).strip() if authors_match else ""
    
    return authors

def getAbstract(pdf):
    """
    Extracts the abstract from the PDF, first using the metadata and then multiple regex to achieve the highest accurency possible
    """
    text = pdf.pages[0].extract_text()
    abstract_regex = re.compile(r"Abstract ?.?\.? ?((?:.|\n)*?)\n[1-9I]\.?\s+") # Abstract\.? ?((?:.|\n)*?)\n[1-9A-Z]\.?\s+(?:INTRODUCTION|Introduction)
    abstract_match = re.findall(abstract_regex, text)
    abstract = abstract_match.pop() if abstract_match else ""
    if abstract == "":
        abstract_regex = re.compile(r"(Abstract ?.?\.? ?)|(In this article|This article presents)((?:.|\n)*?)\n[1-9I]\.?\s+") # Abstract\.? ?((?:.|\n)*?)\n[1-9A-Z]\.?\s+(?:INTRODUCTION|Introduction)
        abstract_match = re.findall(abstract_regex, text)
        abstract = abstract_match.pop() if abstract_match else ""
    finalAbstract=""
    for i in abstract:
        finalAbstract+=i
    return finalAbstract.replace('-\n','')

def extract_pdf_info(file_path):
    """
    Extracts the name of the file, the title of the paper, the authors, and the abstract
    from a PDF file using regular expressions.
    """
    with open(file_path, "rb") as f:
        pdf = PdfReader(f)
        metadata = pdf.metadata
        text = ""
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            text += page.extract_text()

    return (os.path.basename(file_path), getTitle(metadata,text), getAuthors(metadata,text), getAbstract(pdf),text)

def extract_pdf_info_from_directory(directory):
    """
    Extracts the name of the file, the title of the paper, the authors, and the abstract
    from all the PDF files in a directory.
    """
    results = []
    for file_name in os.listdir(directory):
        if file_name.endswith(".pdf"):
            file_path = os.path.join(directory, file_name)
            info = extract_pdf_info(file_path)
            results.append(info)
    return results

def convertPdfToText(file_path):
    """
    Converts a PDF to a string containing all the text 
    """
    with open(file_path, "rb") as f:
        # Read the PDF file with PyPDF2's PdfReader
        pdf = PdfReader(f)
        metadata = pdf.metadata
        text = ""
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            text += transformAccent(page.extract_text())
    return (text,metadata,pdf)

def writeTxt(file_name,output_file_name,text,metadata,pdf):
    """
    Writes all the capital information in a .txt file
    """
    outputString = "Nom du fichier : "+file_name+"\n"
    outputString+="Titre de l'article : "+getTitle(metadata,text)+"\n"
    outputString+="Auteurs : "+"\n"
    outputString+="Résumé de l'article :\n"+getAbstract(pdf)+"\n"
    outputString+="Bibliographie : "
    if(output_file_name!=""):
        fd = os.open(output_file_name,flags=os.O_RDWR|os.O_CREAT|os.O_TRUNC)
        text = str.encode(outputString)
        lgtext = os.write(fd,text)
        if(lgtext==0):
            sys.stderr("Aucune données n'a pu être extraite")
        os.close(fd)
    return outputString


def writeXML(file_name,output_file_name,text,metadata,pdf):
    """
    Writes all the capital information in a .xml file with an XML layout
    """
    outputXML = "<article>\n"
    outputXML+="\t<preamble>"+file_name+"</preamble>\n"
    outputXML+="\t<titre>"+getTitle(metadata,text)+"</titre>\n"
    outputXML+="\t<auteurs>"


    outputXML+="\n\t</auteurs>\n"
    outputXML+="\t<abstract> "+getAbstract(pdf).replace("\n"," ")+" </abstract>\n"
    outputXML+="\t<biblio> "+" </biblio>\n"
    
    outputXML+= "</article>"
    if(output_file_name!=""):
        fd = os.open(output_file_name,flags=os.O_RDWR |os.O_CREAT | os.O_TRUNC)
        text = str.encode(outputXML)
        lgtext = os.write(fd,text)
        if(lgtext==0):
            sys.stderr("Aucune données n'a pu être extraite")
        os.close(fd)
    return outputXML

def launchExtraction(args):
    argsList = vars(args)
    #print(args)
    output_file_name = ""
    if(argsList['out']!=None) : 
            output_file_name = argsList['out']
    text,metadata,pdf = convertPdfToText(argsList['filename'])
    if(argsList['t']==True) :
            return writeTxt(os.path.basename(argsList['filename']),output_file_name,text,metadata,pdf)
    if(argsList['x']==True) : 
            return writeXML(os.path.basename(argsList['filename']),output_file_name,text,metadata,pdf)
    

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parser for scientific papers")
    parser.add_argument('-t',action='store_true',help='To be set if the output should be saved in a .txt')
    parser.add_argument('-x',action='store_true',help='To be set if the output should be saved in a .xml')
    parser.add_argument('filename',help='The path to the file that needs to be converted')
    parser.add_argument('--out',help='Optionnal path to the directory where the output should be saved')
    args = parser.parse_args()
    launchExtraction(args)
