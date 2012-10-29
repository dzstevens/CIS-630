import pickle	
	
def main():
	keys = []
	
	with open('lookup.pkl', 'rb') as f:
		keys = pickle.load(f)
	
	post = {}
	with open('posterior.tsv') as f:
		for l in f:
			line = l.strip().split('\t')
			node = keys[int(line[0])]
			val = round(float(line[1]), 3)
			if val == 0.001:
				val = 0.0
			elif val == 0.999:
				val = 1.0
			post[node] = str(val)
				
	with open('posterior_processed.tsv', 'w') as f:
		for k in sorted(post):
			f.write(k + '\t' + post[k] + '\n')	

if __name__ == '__main__':
	main()