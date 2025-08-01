import sys
import os
import subprocess
from .nftsim_generator_FUNCTIONS import list_files, nftsim_run

def gen_outputs(conf_dir, output_dir, batch, nft_path, n_tasks_per_job = 40):
    """
    Given a directory containing .conf files, will write and submit batch jobs to parallelize .output file generation.
    """

    conf_files = list_files(conf_dir, full_path = True, extension_filter = '.conf')
    if not os.path.exists(output_dir): os.makedirs(output_dir)
        
          
    if batch:
        unique_jobs = {}
        for conf_num in range(0, len(conf_files), n_tasks_per_job):
            chunk = conf_files[conf_num:conf_num + n_tasks_per_job]
            unique_jobs[f'SynPy-nftsim-parallel_job-{conf_num//n_tasks_per_job+1}'] = chunk
        
        for job_name, conf_chunks in unique_jobs.items():
            job_submit_file = job_name + '_job_submit.sh'
            job_status_file = job_name + '_job_status.out'
            nftsim_job_lines = []
            for conf_file in conf_chunks:
                output_file = conf_file.replace(conf_dir, output_dir).replace('.conf', '.output')
                
                nftsim_job_lines.append(f'  {nft_path} -i {conf_file} -o {output_file}')
            
            job_script_path = os.path.join(conf_dir, job_submit_file)
            
            newline_str = '\n'

            slurm_job_script = \
            f"""#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node={len(nftsim_job_lines)}
#SBATCH --output {os.path.join(output_dir, job_status_file)}
#SBATCH --open-mode append
#SBATCH --time=0:30:00
#SBATCH --job-name {job_name}

# Turn off implicit threading in Python, R
export OMP_NUM_THREADS=1

module load NiaEnv/2019b gnu-parallel
module load python/3.8.5
module load gcc/9.4.0

parallel --joblog job.log -j $SLURM_TASKS_PER_NODE <<EOF
{newline_str.join(nftsim_job_lines)}
EOF

# Proceed only once the job has concluded processing, opening, writing, and closing all files; mitigates race conditions
#SBATCH --dependency=afterok:$SLURM_JOB_ID {job_script_path}
echo -n "$SLURM_JOB_ID done" >> {os.path.join(output_dir, job_name + '_done.txt')}
            """
            open(job_script_path, 'w+').write(slurm_job_script)
            cmdstr = f'sbatch {job_script_path}'
            
            subproc = subprocess.run(cmdstr, shell = True, capture_output = True)
            if subproc.returncode == 0:
                output = subproc.stdout.decode(); print(output)
            else:
                print(f'{cmdstr} failed with return code {subproc.returncode}') # error 127 = ssh into a compute (non-login) node
                sys.exit()

        return len(unique_jobs) # return the total number of unique jobs
    
    elif batch == False:
        for conf_file in conf_files:
            output_file = conf_file.replace(conf_dir, output_dir).replace('.conf', '.output')

            # Generate .output file from .conf file
            nftsim_run(nftsim_path = nft_path, 
                       conf_path = conf_path, 
                       output_path = output_file,
                       load_gcc = True)

            print(f'Output file: {os.path.basename(output_file)} complete')
            print('===============')