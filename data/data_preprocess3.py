import pandas as pd
import numpy as np
from pandas import DataFrame
import os
# from rdkit import Chem
from rdkit.Chem import PandasTools
from rdkit.Chem.inchi import MolToInchiKey
import argparse
from tqdm import tqdm



def print_args(args):
    """Print arguments.
    (borrowed from Megatron code https://github.com/NVIDIA/Megatron-LM)"""

    print('arguments:', flush=True)
    for arg in vars(args):
        dots = '.' * (29 - len(arg))
        print('  {} {} {}'.format(arg, dots, getattr(args, arg)), flush=True)

# process spectra generated by NEIMS and divide it to mz, intensities 
def process_spec(df):
    df2 = df.copy()
    new_df = pd.DataFrame()
    all_i = []
    all_mz = []
    for row in range(len(df2)):
        spec = df2["PREDICTED SPECTRUM"][row].split("\n")
        mz = []
        i = []
        spec_max = 0
        for t in spec:
            j,d = t.split()
            j,d = int(j), float(d)
            if spec_max < d:
                spec_max  = d
            mz.append(j)
            i.append(d)
        all_mz.append(mz)
        all_i.append(np.around(np.array(i)/spec_max, 2))
    new_df = DataFrame.from_dict({"mz": all_mz, "intensity": all_i})
    df2 = pd.concat([df2, new_df], axis=1)
    df2 = df2.drop(["PREDICTED SPECTRUM"], axis=1)
    return df2
        
        
def main():
    parser = argparse.ArgumentParser(description="Parse data preparation args")

    parser.add_argument("--load-generated-sdf", type=str, required=True,
                        help="absolute path for loading a .sdf file with generated spectra by NEIMS")
    parser.add_argument("--max-mz", type=int, default=499,
                        help="Filtering out spectra with higher mz than this value")
    parser.add_argument("--max-peaks", type=int, default=200,
                        help="Filtering out spectra with more peaks than this value")
    parser.add_argument("--save-pickle-path", type=str, required=True,
                        help="absolute path for saving a .sdf file with filtered and enriched data")
    
    
    args = parser.parse_args()
    print_args(args)
    
    # load the pickle from the first phase
    print("\n\n##### PHASE 3: LOADING GENERATED SPECTRA #####")
    df = PandasTools.LoadSDF(args.load_generated_sdf, idName="zinc_id", molColName='Molecule')
    
    # processing spectra
    print("##### PROCESSING SPECTRA #####")
    df = process_spec(df)

    # filtering high MZs
    print("##### FILTERING HIGH MZs #####")
    df = df.loc[[x[-1]<= args.max_mz for x in tqdm(df["mz"])]]
    print(f"data len: {len(df)}")
    
    # filtering long spectra
    print("##### FILTERING LONG SPECTRA #####")
    df = df.loc[[len(x) <= args.max_peaks for x in tqdm(df["mz"])]]
    
    # drop unnecessary columns
    df = df[["destereo_smiles", "mz", "intensity"]]
    print(f"the length after all filters: {len(df)}")
    # save th df
    print("##### SAVING destereo_smiles mz intensity  #####")
    df.to_pickle(args.save_pickle_path)
    
    print(f"##### len after PHASE3: {len(df)}")
    
if __name__ == "__main__":
    main()    