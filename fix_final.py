with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    content = f.read()

append = """
    });
}

function selectChild(childId, el) {
    document.querySelectorAll('.child-chip').forEach(function(c) { c.classList.remove('selected'); });
    el.classList.add('selected');
    document.querySelectorAll('.dash-main').forEach(function(d) { d.classList.remove('active'); });
    document.getElementById('dash-' + childId).classList.add('active');
}

document.getElementById('einLauncher').addEventListener('dblclick', function() { toggleEinFloat(); });
</script>
{% endblock %}
"""

new_content = content + append
with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Done. New length:', len(new_content))
