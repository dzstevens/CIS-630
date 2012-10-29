from collections import defaultdict

def main():
	prior = dict()
	post = dict()
	with open('prior_unprocessed.tsv') as f:
		for l in f:
			line = l.strip().split("\t")
			prior[line[0]] = line[1]
			
	with open('posterior_processed.tsv') as f:
		for l in f:
			line = l.strip().split("\t")
			post[line[0]] = line[1]
			
	if set(prior) != set(post):
		print("ERROR:\n\tPrior and Posterior sets unequal!")
		print("\t# of values in Prior but not in Posterior: {}".format(len(set(prior) - set(post))))
		print("\t# of values in Posterior but not in Prior: {}\n".format(len(set(post) - set(prior))))
		return
		
	with open('diff.out', 'w') as f:
		changes = defaultdict(list)
		for k in sorted(prior):
			change = round(float(prior[k]), 3) - round(float(post[k]), 3)
			if change:
				c = 'INC' if change < 0 else 'DEC'
				changes[c].append("{0:<75}\t{1:<5}\t{2:<5}\n".format(k, prior[k], post[k]))
		header = "{0:<75}\t{1:<5}\t{2:<5}\n{3:<6}\n".format('Value', 'Prior', 'Post','-'*90)
		f.write('Increases:\n\n')
		f.write(header)
		for s in changes['INC']:
			f.write(s)
		f.write('\n\nDecreases:\n\n')
		f.write(header)
		for s in changes['DEC']:
			f.write(s)
			
if __name__ == '__main__':
	main()