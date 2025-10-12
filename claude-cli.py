#!/usr/bin/env python
"""Simple Claude CLI wrapper using the Anthropic Python SDK"""

import os
import sys
import anthropic

def main():
    # Get API key from environment variable
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print('Error: ANTHROPIC_API_KEY environment variable not set', file=sys.stderr)
        print('', file=sys.stderr)
        print('Set your API key with:', file=sys.stderr)
        print('  export ANTHROPIC_API_KEY=your-api-key-here', file=sys.stderr)
        print('', file=sys.stderr)
        print('Get your API key from: https://console.anthropic.com/settings/keys', file=sys.stderr)
        sys.exit(1)

    # Get prompt from command line arguments
    if len(sys.argv) < 2:
        print('Usage: claude-cli.py "your prompt here"', file=sys.stderr)
        print('', file=sys.stderr)
        print('Examples:', file=sys.stderr)
        print('  ./claude-cli.py "What is Python?"', file=sys.stderr)
        print('  ./claude-cli.py "Explain quantum computing in simple terms"', file=sys.stderr)
        print('  ./claude-cli.py "Write a bash script to backup files"', file=sys.stderr)
        sys.exit(1)

    prompt = ' '.join(sys.argv[1:])

    # Create Anthropic client
    client = anthropic.Anthropic(api_key=api_key)

    # Send message to Claude
    print(f'Asking Claude: {prompt}\n')
    print('-' * 80)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Print response
        print(message.content[0].text)
        print('-' * 80)

    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
