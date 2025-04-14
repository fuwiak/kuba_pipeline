#!/bin/bash

# Create the main project directory
mkdir -p my_feast_kubeflow_project

# Create the feast_feature_repo directory and subdirectories
mkdir -p my_feast_kubeflow_project/feast_feature_repo/data
touch my_feast_kubeflow_project/feast_feature_repo/feature_store.yaml
touch my_feast_kubeflow_project/feast_feature_repo/example_feature_view.py

# Create the pipeline directory and components
mkdir -p my_feast_kubeflow_project/pipeline/pipeline_components
touch my_feast_kubeflow_project/pipeline/pipeline_components/ingest_data_component.py
touch my_feast_kubeflow_project/pipeline/pipeline_components/train_model_component.py
touch my_feast_kubeflow_project/pipeline/pipeline_components/evaluate_and_deploy_component.py
touch my_feast_kubeflow_project/pipeline/pipeline_definition.py
touch my_feast_kubeflow_project/pipeline/requirements.txt

# Create the kserve directory
mkdir -p my_feast_kubeflow_project/kserve
touch my_feast_kubeflow_project/kserve/kserve_inference_service.yaml

# Create the scripts directory
mkdir -p my_feast_kubeflow_project/scripts
touch my_feast_kubeflow_project/scripts/test_inference.py

# Create the installation directory
mkdir -p my_feast_kubeflow_project/installation
touch my_feast_kubeflow_project/installation/install_kubeflow_on_kind.sh
touch my_feast_kubeflow_project/installation/install_feast_in_cluster.sh

# Create the documentation directory
mkdir -p my_feast_kubeflow_project/doc
touch my_feast_kubeflow_project/doc/short_explanation_of_data_flow.pdf

# Create the README
touch my_feast_kubeflow_project/README.md

echo "Directory structure created successfully!"