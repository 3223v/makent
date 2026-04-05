"""
MySQL 数据库表查询工具
用于连接本地 MySQL 数据库并查询所有表
"""

import pymysql
from typing import List, Dict, Any
import os

def get_mysql_tables(host: str = "localhost", port: int = 3306, user: str = "root", 
                     password: str = "", database: str = None) -> List[Dict[str, Any]]:
    """
    连接 MySQL 数据库并获取所有表信息
    
    Args:
        host: MySQL 主机地址，默认 localhost
        port: MySQL 端口，默认 3306
        user: 用户名，默认 root
        password: 密码，默认空
        database: 数据库名，如果为 None 则查询所有数据库的表
    
    Returns:
        包含表信息的字典列表，每个字典包含: table_name, database, table_rows, create_time等
    """
    try:
        # 建立连接
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        tables_info = []
        
        with connection.cursor() as cursor:
            if database:
                # 查询指定数据库的表
                cursor.execute("SHOW TABLES")
                results = cursor.fetchall()
                for row in results:
                    table_name = list(row.values())[0]
                    
                    # 获取表的详细信息
                    cursor.execute(f"SHOW TABLE STATUS FROM `{database}` LIKE '{table_name}'")
                    table_status = cursor.fetchone()
                    
                    if table_status:
                        tables_info.append({
                            "table_name": table_name,
                            "database": database,
                            "table_rows": table_status.get("Rows", 0),
                            "create_time": str(table_status.get("Create_time", "")),
                            "update_time": str(table_status.get("Update_time", "")),
                            "engine": table_status.get("Engine", ""),
                            "comment": table_status.get("Comment", "")
                        })
            else:
                # 查询所有数据库的表
                cursor.execute("SHOW DATABASES")
                databases = cursor.fetchall()
                
                for db_row in databases:
                    db_name = list(db_row.values())[0]
                    # 跳过系统数据库
                    if db_name in ['information_schema', 'mysql', 'performance_schema', 'sys']:
                        continue
                    
                    try:
                        cursor.execute(f"SHOW TABLES FROM `{db_name}`")
                        tables = cursor.fetchall()
                        
                        for table_row in tables:
                            table_name = list(table_row.values())[0]
                            
                            # 获取表的详细信息
                            cursor.execute(f"SHOW TABLE STATUS FROM `{db_name}` LIKE '{table_name}'")
                            table_status = cursor.fetchone()
                            
                            if table_status:
                                tables_info.append({
                                    "table_name": table_name,
                                    "database": db_name,
                                    "table_rows": table_status.get("Rows", 0),
                                    "create_time": str(table_status.get("Create_time", "")),
                                    "update_time": str(table_status.get("Update_time", "")),
                                    "engine": table_status.get("Engine", ""),
                                    "comment": table_status.get("Comment", "")
                                })
                    except Exception as e:
                        # 如果无法访问某个数据库，跳过
                        continue
        
        connection.close()
        return tables_info
        
    except Exception as e:
        raise Exception(f"连接 MySQL 失败: {str(e)}")

# 工具定义
tool = {
    "name": "mysql_tables",
    "description": "连接本地 MySQL 数据库并查询所有表信息，包括表名、数据库名、行数、创建时间等",
    "parameters": {
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "description": "MySQL 主机地址，默认 localhost"
            },
            "port": {
                "type": "integer",
                "description": "MySQL 端口，默认 3306"
            },
            "user": {
                "type": "string",
                "description": "数据库用户名，默认 root"
            },
            "password": {
                "type": "string",
                "description": "数据库密码，默认空"
            },
            "database": {
                "type": "string",
                "description": "指定要查询的数据库名，不指定则查询所有数据库的表"
            }
        },
        "required": []
    },
    "func": get_mysql_tables
}