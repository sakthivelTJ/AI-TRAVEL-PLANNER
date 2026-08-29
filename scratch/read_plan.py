content = open('scratch/plan_output.html', encoding='utf-8').read()
idx = content.find('id="plan-content"')
if idx != -1:
    print("FOUND DIV CONTENT:")
    print(content[idx:idx+1200])
else:
    print("plan-content div NOT FOUND")
