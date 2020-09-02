import re
def three_number_after_dot(content):
    if '.' not in content and len(content) >= 3:
        content = content[:-3] + '.' + content[-3:]
    return content


def remove_douhao(content:str):
    return content.replace(',','')

def replace__A(content):
    return re.sub('_{2,}A', 'EA', content)
