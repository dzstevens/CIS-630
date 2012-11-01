import re
import pickle
from math import exp
from collections import defaultdict, Counter


def sigmoid(x):
    if abs(x) > 7:
        return 0.001 if x < 0 else .999
    else:
        sig = 1 / (1 + exp(-x))
        return round(sig, 3)


def main():
    prior =  defaultdict(lambda: 1.0)
    edges =  dict()
    ignores = set()
    r = re.compile(r'(!?\w+\([^()]+\))|(\d+.?\d*)')
    print('Parsing Errors:\n')
    with open('groundings.in') as f:
        line_num = 1
        for l in f:
            line = [x[0] if x[0] else x[1] for x in r.findall(l)]
            if len(line) == 2:
                neg = line[0][0] == '!'
                node = line[0][1:] if neg else line[0]
                val = float(line[1])
                if neg:
                    val *= -1
                prior[node] += val
            elif len(line) == 3:
                source = line[0][1:] if line[0][0] == '!' else line[0]
                dest = line[1][1:] if line[1][0] == '!' else line[1]
                edges[(source, dest)] = float(line[2])
            else:
                print('Line {}:\n\t" {} "'.format(line_num, l.strip()))
            line_num+=1

    keys = list(sorted(prior))
    indices = dict()
    u_lines = 0
    with open('prior_unprocessed.tsv', 'w') as f:
        for k in keys:
                v = prior[k] = sigmoid(prior[k])
                f.write('{}\t{}\t{}\n'.format(k, v, round(1.0 - v, 3)))
                u_lines += 1

    p_lines = 0
    with open('prior_processed.tsv', 'w') as f:
        i = 0
        for k in keys:
            f.write('{}\t{}\t{}\n'.format(i, v, round(1.0 - v, 3)))
            indices[k] = i
            i+=1
            p_lines += 1

    assert p_lines == u_lines, "Prior improperly processed"

    missing_nodes = Counter()
    p_lines = 0
    with open('edges_processed.tsv', 'w') as f:
        to_remove = []
        for k, v in edges.items():
            try:
                source = indices[k[0]]
                dest = indices[k[1]]
                f.write('{}\t{}\t{}\n'.format(source, dest, v))
                p_lines += 1
            except (KeyError) as e:
                for key in set(e.args):
                    missing_nodes[key] += 1
                to_remove.append(k)
            except:
                raise
        for k in to_remove:
            del edges[k]

    u_lines = 0
    with open('edges_unprocessed.tsv', 'w') as f:
        for k, v in edges.items():
            f.write('{}\t{}\t{}\n'.format(k[0], k[1], v))
            u_lines += 1
            
    assert p_lines == u_lines, "Edges improperly processed"

    print('Missing nodes:\n')
    print('{0:<100}\t{1:<3}'.format('Node Value', 'Count'))
    for node in sorted(missing_nodes):
        print('{0:<100}\t{1:<3}'.format(node, missing_nodes[node]))

    print('\nTotal missing:',len(missing_nodes))

    with open('lookup.pkl', 'wb') as f:
        pickle.dump(keys, f)


if __name__ == '__main__':
    main()