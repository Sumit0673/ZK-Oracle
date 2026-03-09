import os
import sys

# Search in the current venv's site-packages
site_packages = [p for p in sys.path if 'site-packages' in p]

if not site_packages:
    print("Could not find site-packages in sys.path")
    sys.exit(1)

target = site_packages[0]
print(f"Searching in: {target}")

found = []
for root, dirs, files in os.walk(target):
    if 'langchain' in root:
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'class AgentExecutor' in content:
                            found.append(('AgentExecutor', path))
                        if 'def create_tool_calling_agent' in content:
                            found.append(('create_tool_calling_agent', path))
                except Exception:
                    continue

if found:
    print("\nResults:")
    for name, f in found:
        # Convert absolute path to a relative import-like string
        rel = os.path.relpath(f, target)
        module = rel.replace('.py', '').replace('/', '.')
        if module.endswith('.__init__'):
            module = module[:-9]
        print(f"  [{name}] in: {module}")
else:
    print("\n'AgentExecutor' not found in site-packages.")
