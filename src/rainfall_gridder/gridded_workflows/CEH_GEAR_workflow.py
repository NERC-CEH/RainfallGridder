from rainfall_gridder.prepare_data.DataPreparer import DataPreparer
from rainfall_gridder.quality_control import apply_intenseQC_rulebase 
from rainfall_gridder.generate_grids import ceh_gear_subdaily_producer


from rainfall_gridder.config.configs import CEH_GEAR_CONFIG
from rainfall_gridder.config.schema import WorkflowConfig

def ceh_gear_subdaily_workflow(config: WorkflowConfig=CEH_GEAR_CONFIG):
    # 1. Prepare data
    data, metadata = DataPreparer(config.metadata)

    # 2. Quality Control
    data, metadata = apply_intenseQC_rulebase(data, metadata, config.output_dir)

    # 3. Generate grids
    data, metadata = ceh_gear_subdaily_producer(data, metadata, config.output_dir)
    
    # 4. Save outputs
    return