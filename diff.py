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
		print("Values in Prior but not in Posterior:\n")
		for v in set(prior) - set(post):
			print(v)
			
		print("Values in Posterior but not in Prior:\n")
		for v in set(post) - set(prior):
			print(v)
		return
		
	with open('diff.out', 'w') as f:
		f.write("{0:<75}\t{1:<5}\t{2:<5}\t{3:<6}\n{4}\n".format('Value', 'Prior', 'Post', 'Change','-'*98))
		for k in sorted(prior):
			change = round(float(prior[k]), 3) - round(float(post[k]), 3)
			if change:
				c = 'INC' if change < 0 else 'DEC'
				f.write("{0:<75}\t{1:<5}\t{2:<5}\t{3:>6}\n".format(k, prior[k], post[k], c))
	
if __name__ == '__main__':
	main()