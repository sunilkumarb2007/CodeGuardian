with open('generate_demo_data.py', 'r') as f:
    content = f.read()

content = content.replace("'active'", "'authorized'")

with open('generate_demo_data.py', 'w') as f:
    f.write(content)
