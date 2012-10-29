from collections import defaultdict, Counter
import re
import pickle

def main():
	prior =	 defaultdict(lambda: 1.0)
	edges =	 dict()
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
				if val > 1.0:
					prior[node] = 0.001 if neg else 0.999
					ignores.add(node)
				elif node not in ignores:
					prior[node] = min(prior[node], val)
				prior[node] = round(prior[node], 3)
				if prior[node] == 0:
					prior[node] += .001
				elif prior[node] == 1:
					prior[node] -= .001 
			elif len(line) == 3:
				source = line[0][1:] if line[0][0] == '!' else line[0]
				dest = line[1][1:] if line[1][0] == '!' else line[1]
				edges[source] = dest
			else:
				print('Line {0}:\n\t" {1} "'.format(line_num, l.strip(), len(line)))
			line_num+=1
			
	keys = list(sorted(prior))
	with open('prior_unprocessed.tsv', 'w') as f:
		for k in keys:
			v = round(prior[k], 3)
			if v == .999:
				v = 1.0
			elif v == .001:
				v = 0.0
			f.write(k + '\t' + str(v) + '\n')
	
	indices = dict()
	with open('prior.tsv', 'w') as f:
		i = 0
		for k in keys:
			f.write(str(i) + '\t' + str(round(prior[k],3)) + '\t' + str(round(1.0 - prior[k],3)) + '\n')
			indices[k] = i
			i+=1
	  
	with open('edges_unprocessed.tsv', 'w') as f:
		for k, v in edges.items():
			f.write(k + '\t' + v + '\n')
	
	missing_nodes = Counter()
	with open('edges.tsv', 'w') as f:
		for k, v in edges.items():
			try:
				f.write(str(indices[k]) + '\t' + str(indices[v]) + '\n')
			except (KeyError) as e:
				for key in set(e.args):
					missing_nodes[key] += 1
					
	print('Missing nodes:\n')
	print('{0:<100}\t{1:<3}'.format('Node Value', 'Count'))
	for node in sorted(missing_nodes):
		print('{0:<100}\t{1:<3}'.format(node, missing_nodes[node]))
	
	print('\nTotal missing: '+str(len(missing_nodes)))
	
	with open('lookup.pkl', 'wb') as f:
		pickle.dump(keys, f)
	
if __name__ == '__main__':
	main()