#!/usr/bin/env python3
"""
Script to verify environment variables are being loaded correctly.
Run this script with: python check_env.py
"""

import os
from dotenv import load_dotenv
import sys


def main():
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")

    # Try to load environment variables
    print("\nLoading .env file...")
    load_dotenv()

    # Check for API keys and variables
    print("\nChecking environment variables:")

    # Check for Anthropic API key
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    print(
        f"ANTHROPIC_API_KEY: {'Found (first 10 chars: ' + anthropic_key[:10] + '...)' if anthropic_key else 'NOT FOUND'}")

    # Check for Redis configuration
    redis_host = os.getenv('REDIS_HOST')
    redis_port = os.getenv('REDIS_PORT')
    redis_password = os.getenv('REDIS_PASSWORD')

    print(f"REDIS_HOST: {redis_host or 'NOT FOUND'}")
    print(f"REDIS_PORT: {redis_port or 'NOT FOUND'}")
    print(f"REDIS_PASSWORD: {'Found (hidden)' if redis_password else 'NOT FOUND'}")

    # Check for AWS credentials
    aws_region = os.getenv('AWS_REGION')
    aws_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')

    print(f"AWS_REGION: {aws_region or 'NOT FOUND'}")
    print(f"AWS_ACCESS_KEY_ID: {'Found (hidden)' if aws_key else 'NOT FOUND'}")
    print(f"AWS_SECRET_ACCESS_KEY: {'Found (hidden)' if aws_secret else 'NOT FOUND'}")

    # Verify file existence
    env_file = os.path.join(os.getcwd(), '.env')
    print(f"\n.env file exists: {os.path.exists(env_file)}")

    if os.path.exists(env_file):
        print(f".env file permissions: {oct(os.stat(env_file).st_mode)[-3:]}")
        print(f".env file size: {os.path.getsize(env_file)} bytes")

    # Print .env file path
    print(f"\nAbsolute path to .env file: {os.path.abspath('.env')}")

    # Verify we can see the right content
    print("\nLooking for environment variables directly in the .env file...")
    try:
        with open('.env', 'r') as f:
            content = f.read()
            if 'ANTHROPIC_API_KEY' in content:
                print("✓ ANTHROPIC_API_KEY found in .env file")
            else:
                print("✗ ANTHROPIC_API_KEY not found in .env file")
    except Exception as e:
        print(f"Error reading .env file: {e}")


if __name__ == "__main__":
    main()
