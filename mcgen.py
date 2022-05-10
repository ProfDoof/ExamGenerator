#!/bin/python3
from io import TextIOWrapper
from pathlib import Path
import subprocess
import uuid

import click

@click.command()
@click.argument("file", type=click.File())
@click.argument("output", type=click.Path(path_type=Path))
@click.option("--makeup", is_flag=True)
def convert(file: TextIOWrapper, output: Path, makeup: bool):
    """Converts Multiple Choice Test FILE to a formatted PDF written to the path provided by OUTPUT"""

    # Allow for 1. 1. 1. notation instead of requiring that order be right  
    convert = {
        1: 'a',
        2: 'b',
        3: 'c',
        4: 'd',
    }
    ak_lines: list[str] = []
    test_lines: list[str] = []

    numAns = 0
    numQuestions = 0
    foundAns = True
    question = ""
    shortAnswer = None
    for line in file:
        partition = line.partition('.')
        if line.startswith('```shortanswer'):
            foundAns = True
            shortAnswer = True
            test_lines.append('Short Answer:\n\\vspace{4cm}\n')
            ak_lines.pop()
            ak_lines.append(f'\\item \n')
        elif shortAnswer and line.startswith('```'):
            shortAnswer = None
            ak_lines.append('\n')
        elif shortAnswer:
            ak_lines.append(line)
        elif line.startswith('### '):
            if not foundAns:
                raise Exception(f'Question {numQuestions} doesn\'t have an answer: \n{question}')
            if makeup and shortAnswer != None:
                test_lines.append(f'Explain why for question {numQuestions} the correct answer is correct and why each incorrect answer is incorrect:\n\\vspace{{5cm}}\n\n\n')
            
            numAns = 0
            numQuestions += 1
            question = line.lstrip('#').lstrip()
            question = '### \\wideunderline[.75cm]{} ' + str(numQuestions) + f'. {question}'
            test_lines.append(question)
            answer_start = f'\\item \\wideunderline[1cm]{{'
            ak_lines.append(answer_start)
            foundAns = False
            shortAnswer = False
        elif line.startswith('# '):
            test_lines.append(line)
            ak_lines.append(line.rstrip() + ' Answer Key\n\\begin{multicols}{3}\n\\begin{enumerate}\n')
        elif partition[0] == line:
            test_lines.append(line)
        elif partition[0].isdigit():
            numAns += 1
            answer = line[2:]
            option = convert[numAns]
            if answer.lstrip().startswith('\\*'):
                if foundAns:
                    raise Exception(f'Question {numQuestions} has more than one answer\n{question}')
                foundAns = True
                answer = answer.lstrip()[2:]
                ak_lines.extend([option, '}\n'])
            test_lines.append(option + ')' + answer)
        else:
            test_lines.append(line)

    if not foundAns:
        raise Exception(f'Question {numQuestions} doesn\'t have an answer: \n{question}')
    ak_lines.append('\\end{enumerate}\n\\end{multicols}\n')
    output = output.resolve()
    temp_id = uuid.uuid1()
    pdfgenfile = output.parent / (str(temp_id) + '.md')
    ansgenfile = output.parent / (str(temp_id) + 'Ans.md')  
    with open(pdfgenfile, 'w') as pdfgen:
        pdfgen.writelines(test_lines)
    with open(ansgenfile, 'w') as ansgen:
        ansgen.writelines(ak_lines)
    cur = Path(__file__).absolute().parent
    print(f'{cur / "before.tex"}')
    cmd = f'pandoc -H {cur / "before.tex"} -f markdown+raw_tex --listings --highlight-style tango --lua-filter=/home/john/.pandoc/filters/diagram-generator.lua -t latex -o {output.resolve()} {pdfgenfile}'
    print(cmd)
    res = subprocess.call(cmd, shell = True)
    print("Returned Value: ", res)
    cmd = f'pandoc -H {cur / "before.tex"} -f markdown+raw_tex --listings --highlight-style tango --lua-filter=/home/john/.pandoc/filters/diagram-generator.lua -t latex -o {output.parent / output.stem}Ans.pdf  {ansgenfile}'
    print(cmd)
    res = subprocess.call(cmd, shell = True)
    print("Returned Value: ", res)
    pdfgenfile.unlink()
    ansgenfile.unlink()
