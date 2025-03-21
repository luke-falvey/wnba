set -xe

# Create deployment package
mkdir -p package
uv pip install --no-cache --target package .
cd package
zip -r ../terraform/lambda_function_payload.zip .
cd ..

## Run terraform

cd terraform
terraform apply -auto-approve
cd ..

# Clean up
rm -rf package
rm terraform/lambda_function_payload.zip

