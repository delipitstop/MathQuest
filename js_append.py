
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
