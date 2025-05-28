import csv
from sqlalchemy import create_engine, inspect
import re

# 你的数据库连接URL
DATABASE_URL = "postgresql+psycopg2://fastsoy:Fastsoy*132!@10.68.130.11:15432/multi_tenant"

# 提取 models 字段中文描述

def extract_field_comments(model_path):
    table_comments = {}
    current_table = None
    with open(model_path, encoding='utf-8') as f:
        for line in f:
            m_table = re.match(r'class (\w+)\(.*?\):', line)
            if m_table:
                current_table = m_table.group(1)
                table_comments[current_table] = {}
            m_field = re.match(r'\s*(\w+)\s*=\s*Column\([^)]+comment\s*=\s*[\'\"](.+?)[\'\"]', line)
            if m_field and current_table:
                field, comment = m_field.group(1), m_field.group(2)
                table_comments[current_table][field] = comment
    return table_comments

# 分别提取两个 models 文件
public_comments = extract_field_comments('app/models/public.py')
tenant_comments = extract_field_comments('app/models/tenant.py')

def get_chinese_comment(schema, table, field):
    if schema == 'public':
        comments = public_comments
    else:
        comments = tenant_comments
    for model_table, fields in comments.items():
        if model_table.lower() == table.lower():
            return fields.get(field, '')
    return ''

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)
schemas = ['public', 'tenant_1']

with open('db_schema.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([
        'schema名', '表名', '字段名', '字段类型', '字段长度', '字段描述', '中文描述', '是否主键', '是否自增', '是否唯一',
        '是否可空', '默认值', '外键表', '外键字段', '是否有索引', '其它约束'
    ])
    for schema in schemas:
        for table_name in inspector.get_table_names(schema=schema):
            columns = inspector.get_columns(table_name, schema=schema)
            pk = inspector.get_pk_constraint(table_name, schema=schema).get('constrained_columns', [])
            uniques = {tuple(u['column_names']) for u in inspector.get_unique_constraints(table_name, schema=schema)}
            indexes = {tuple(i['column_names']) for i in inspector.get_indexes(table_name, schema=schema)}
            fks = inspector.get_foreign_keys(table_name, schema=schema)
            fk_map = {}
            for fk in fks:
                for col, ref_col in zip(fk['constrained_columns'], fk['referred_columns']):
                    fk_map[col] = (fk['referred_table'], ref_col)
            for col in columns:
                writer.writerow([
                    schema,
                    table_name,
                    col['name'],
                    str(col['type']),
                    getattr(col['type'], 'length', ''),
                    col.get('comment', ''),
                    get_chinese_comment(schema, table_name, col['name']),
                    '是' if col['name'] in pk else '',
                    '是' if col.get('autoincrement', False) else '',
                    '是' if any(col['name'] in u for u in uniques) else '',
                    '否' if col['nullable'] is False else '是',
                    col.get('default', ''),
                    fk_map[col['name']][0] if col['name'] in fk_map else '',
                    fk_map[col['name']][1] if col['name'] in fk_map else '',
                    '是' if any(col['name'] in i for i in indexes) else '',
                    ''  # 其它约束可根据需要补充
                ])