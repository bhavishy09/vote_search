import pymupdf
import re

doc = pymupdf.open('WithPhoto_GANGAPUR CITY NAGAR PARISHAD-Ward No-020-Part No-001.pdf')
p3 = doc[2]
xobjs = p3.get_xobjects()
s = doc.xref_stream(xobjs[0][0]).decode('latin1', errors='ignore')

def extract_pdf_strings(stream):
    results = []
    i = 0
    bs = chr(92)
    while i < len(stream):
        if stream[i] == '(':
            start = i
            i += 1
            paren_depth = 1
            content = []
            while i < len(stream) and paren_depth > 0:
                if stream[i] == bs and i + 1 < len(stream):
                    c = stream[i+1]
                    if c == '(':
                        content.append('(')
                    elif c == ')':
                        content.append(')')
                    elif c == bs:
                        content.append(bs)
                    elif c == 'n':
                        content.append('\n')
                    elif c == 'r':
                        content.append('\r')
                    elif c == 't':
                        content.append('\t')
                    elif c == 'b':
                        content.append('\b')
                    elif c == 'f':
                        content.append('\f')
                    else:
                        content.append(c)
                    i += 2
                    continue
                elif stream[i] == '(':
                    paren_depth += 1
                    content.append('(')
                elif stream[i] == ')':
                    paren_depth -= 1
                    if paren_depth > 0:
                        content.append(')')
                else:
                    content.append(stream[i])
                i += 1
            results.append((''.join(content), start, i))
        else:
            i += 1
    return results

strings = extract_pdf_strings(s)
print('Total extracted strings on page 3 with proper escape handler:', len(strings))
old_strings = re.findall(r'\(([^\)]*)\)', s)
print('Total extracted strings on page 3 with naive regex:', len(old_strings))

# Let's see differences
diff_count = 0
bs = chr(92)
for st, start, end in strings:
    raw = s[start:end]
    if bs in raw:
        diff_count += 1
        if diff_count <= 10:
            print(f'Raw in PDF: {raw}  -->  Unescaped: {repr(st)}')
print('Strings containing escapes on page 3:', diff_count)
