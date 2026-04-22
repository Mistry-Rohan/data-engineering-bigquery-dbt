{% macro build_trip_id(columns) %}
    to_hex(
        md5(
            concat(
                {% for column in columns %}
                coalesce(cast({{ column }} as string), '')
                {% if not loop.last %}, '|', {% endif %}
                {% endfor %}
            )
        )
    )
{% endmacro %}
