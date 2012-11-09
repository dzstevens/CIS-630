#! /bin/bash

# If not python 3.x return exit code 0
python -c "import sys; sys.exit(0) if sys.version_info[0] == 3 else sys.exit(1)"
# capture exit code of last command
is_python3=$? 
# If python version check failed, exit script with failure
if [ ! $is_python3 -eq 0 ]; then
        echo "ERROR: Python 3.x is required!"
        exit $is_python3
fi

echo "Parsing input..."
echo "Parsing data from 'groundings.in'"
python parse.py > parse.out
echo "Parsing finished."
echo "Unprocessed prior data saved to 'prior_unprocessed.tsv'"
echo "Processed prior data saved to 'prior_processed.tsv'"
echo "Unprocessed edge data saved to 'edges_unprocessed.tsv'"
echo "Processed edge data saved to 'edges_processed.tsv'"
echo "Error output saved to 'parse.out'"
echo
echo "Running through graphical models toolkit..."
../graphlabapi/release/toolkits/graphical_models/lbp_structured_prediction --prior prior_processed.tsv --graph edges_processed.tsv --output posterior.tsv
cat posterior.tsv_* > posterior_unprocessed.tsv
rm posterior*_of_2*
echo "Toolkit finished."
echo "Unprocessed posterior data saved to 'posterior_unprocessed.tsv'"
echo
echo "Processing posterior data..."
python process.py
echo "Processing finished."
echo "Processed posterior data saved to 'posterior_processed.tsv'"
echo
echo "Running comparison..."
python diff.py
echo "Comparison finished."
echo "Diff saved to 'diff.out'"
echo
if [ $# -eq 1 ] && [ $1 == 'clean' ]; then
	echo "Removing generated .tsv's"
	rm *.tsv
	echo
fi
rm *.pkl
echo "Done!"
