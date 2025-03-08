import argparse

import 2v1Evaluation

def i_plus_one_vs_i(max_i, iterations):
    for iteration in range(iterations):
        for i in range(1, max_i + 1):
            2v1Evaluation.main()            


if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Find how accuracy decreases as the number of saboteurs increases.')
    
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Now you can use args.max_i and args.iterations in your code
    max_i = args.max_i
    iterations = args.iterations
    
    # Your code using max_i and iterations goes here
    