import re
from typing import List, Union


# TODO write unit tests for this function as it is taken from braceNotation.js and converted by copilot without proper testing
def encode_brace_notation(data: Union[str, List[str]]) -> List[str]:
    if not isinstance(data, list):
        data = [data]

    node_names = set(data)

    nodes_with_no_number = []
    node_objects = []
    find_digits = re.compile(r"\d+")

    for node in node_names:
        regex_res = find_digits.search(node)
        if regex_res is None:
            nodes_with_no_number.append(node)
        else:
            node_objects.append({
                'preText':
                node[:regex_res.start()],
                'postText':
                node[regex_res.end():],
                'number':
                node[regex_res.start():regex_res.end()]
            })

    groups = []
    while node_objects:
        tmp_elem = node_objects.pop()
        pre_text = tmp_elem['preText']
        post_text = tmp_elem['postText']
        current_group = {
            'preText': pre_text,
            'postText': post_text,
            'number': [tmp_elem['number']]
        }

        for i in range(len(node_objects) - 1, -1, -1):
            if (node_objects[i]['preText'] == pre_text
                    and node_objects[i]['postText'] == post_text):
                current_group['number'].append(node_objects[i]['number'])
                node_objects.pop(i)

        current_group['number'].sort(key=int)
        groups.append(current_group)

    brace_encoded = []
    for elem in groups:
        brace_str = elem['preText'] + "[" + elem['number'][0]

        last_number = elem['number'][0]
        minus_needed = False
        for i in range(1, len(elem['number'])):
            if int(last_number) + 1 == int(elem['number'][i]):
                last_number = elem['number'][i]
                minus_needed = True
            else:
                if minus_needed:
                    brace_str += "-" + last_number
                brace_str += "," + elem['number'][i]
                last_number = elem['number'][i]
                minus_needed = False

        if minus_needed:
            brace_str += "-" + last_number

        brace_str += "]" + elem['postText']
        brace_encoded.append(brace_str)

    return brace_encoded + nodes_with_no_number
