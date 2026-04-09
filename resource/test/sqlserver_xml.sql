case 019 "添加删除列注释" 0
before:
drop table col_comment_t1;
go
use ora_mil
src_sql:
create table col_comment_t1 (
         S_Id        int PRIMARY KEY not null,
         S_StuNo     varchar(50) not null,
         S_Name      varchar(20) not null,
         S_Sex       varchar(10) check (S_Sex='男' or S_Sex='女'),
         S_Height    varchar(20) default '150厘米',
		     By_int1	int default 0,
         By_int2	int default 0,
         By_str1	varchar(20) not null,
         By_str2	varchar(20) not null
);
go
sleep(5000);
EXEC sp_addextendedproperty N'Colcomment_t_Desc1',N'这个是列注释添加删除测试',N'SCHEMA',N'dbo',N'TABLE',N'col_comment_t1', N'COLUMN', N'By_str1';
EXEC sp_addextendedproperty N'Colcomment_t_Desc2',N'空',N'SCHEMA',N'dbo',N'TABLE',N'col_comment_t1', N'COLUMN', N'S_Sex';

EXEC sp_addextendedproperty N'Colcomment_t_Desc3',N'测试拉大锯卡拉胶可垃圾袋刻录机啊金坷垃就看来发金坷垃就发卡拉胶阿卡了记得开了极乐空间看见阿卡丽机房的卡拉胶卡建库的了就按开了开了就爱看来得及付款垃圾看了空间啊刻录机肯德基了',N'SCHEMA',N'dbo',N'TABLE',N'col_comment_t1', N'COLUMN', N'S_Height';
EXEC sp_addextendedproperty N'Colcomment_t_Desc4',N'备注多个jlkaj家看见打开垃圾可垃圾袋刻录机啊开立即付款垃圾开发逻辑卡拉胶阿卡拉法基看来发就按卡拉胶阿卡来得及发注释',N'SCHEMA',N'dbo',N'TABLE',N'col_comment_t1', N'COLUMN', N'By_int2';
EXEC sp_dropextendedproperty N'Colcomment_t_Desc3','SCHEMA', 'dbo','TABLE','col_comment_t1','COLUMN','S_Height';
go

tgt_sql:
select class,class_desc,name,convert(nvarchar(255),value) from sys.extended_properties where major_id = OBJECT_ID('col_comment_t1') order by minor_id;
select * from col_comment_t1 order by S_Id;
select name,xtype,length,isnullable from sys.syscolumns where id = OBJECT_ID('col_comment_t1');
select name,xtype from sys.sysobjects where parent_obj= OBJECT_ID('col_comment_t1') order by name;
select 索引名称=a.name ,表名=c.name ,索引字段名=d.name ,索引字段位置=d.colid  FROM  sysindexes   a JOIN   sysindexkeys   b   ON   a.id=b.id   AND   a.indid=b.indid JOIN   sysobjects   c   ON   b.id=c.id  JOIN   syscolumns   d   ON   b.id=d.id   AND   b.colid=d.colid WHERE   a.indid   NOT IN(0,255) AND   c.name='col_comment_t1'  ORDER BY   c.name,a.name,d.name;
go
CREATE TABLE example_table (
    id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);
ALTER TABLE [ora_mil].[dbo].[example_table] ADD CONSTRAINT DF_example_table_name DEFAULT ('def') FOR name
ALTER TABLE example_table
ALTER COLUMN name add DEFAULT 'default_value';
case 020 "删除注释列" 0
before:
drop table col_comment_t2;
go
src_sql:
create table dbo.col_comment_t2 (
	jioyrq	char(8) not null,
	jgjyls	char(14) not null,
	jczuho	int default 0,
	qjulsh	char(26),
	jiaoym	char(4),
	yxjlts	int default 0,
	sjchuo	char(17),
	jiluzt	char(1),
	record	int default 0,
	hxkbmc	char(30),
	sxjsri	char(8),
	fjxx01	char(30),
	byint1	int default 0,
	byint2	int default 0,
	bystr1	char(20),
	bystr2	char(20),
	primary key(jioyrq,jgjyls)
);
go
sleep(5000);
insert into dbo.col_comment_t2 values ('pfyrq001','pfyhjqjyls001',1,'上海英方有限公司！@#￥%001','2341',101,'This is a 测试','1',1011,'来自英方杭州分公司的测试','test1234',null,10111,101111,'浦发银行测试方案',' ');
insert into dbo.col_comment_t2 values ('pfyrq002','pfyhjqjyls002',2,'上海英方有限公司！@#￥%001','2342',102,'This is a 测试','2',1012,'来自英方杭州分公司的测试','test1234',null,10112,101112,'浦发银行测试方案','快乐健康六角');
EXEC sp_addextendedproperty N'添加列注释no1',N'kldajkjklajkABCDEGEE',N'SCHEMA',N'dbo',N'TABLE',N'col_comment_t2', N'COLUMN', N'bystr1';
EXEC sp_addextendedproperty N'添加列注释no2',N'int类型列注释测试用例',N'SCHEMA',N'dbo',N'TABLE',N'col_comment_t2', N'COLUMN', N'Byint2';
insert into dbo.col_comment_t2 values ('pfyrq003','pfyhjqjyls003',3,'上海英方有限公司！@#￥%002','2343',103,'This is a 测试','3',1013,'来自英方杭州分公司的测试','test1234',null,10113,101113,'浦发银行测试方案','快乐健康六角');
ALTER TABLE dbo.col_comment_t2 drop column bystr1;
insert into dbo.col_comment_t2 values ('pfyrq004','pfyhjqjyls004',4,'上海英方有限公司！@#￥%002','2344',104,'This is a 测试','4',1014,'来自英方杭州分公司的测试','test1234',null,10113,101114,'快乐健康六角');
go
tgt_sql:
select * from dbo.col_comment_t2 order by jczuho;
select class,class_desc,name,convert(nvarchar(255),value) from sys.extended_properties where major_id = OBJECT_ID('col_comment_t2') order by minor_id;
select name,xtype,length,isnullable from sys.syscolumns where id = OBJECT_ID('col_comment_t2');
select name,xtype from sys.sysobjects where parent_obj= OBJECT_ID('col_comment_t2') order by name;
select 索引名称=a.name ,表名=c.name ,索引字段名=d.name ,索引字段位置=d.colid  FROM  sysindexes   a JOIN   sysindexkeys   b   ON   a.id=b.id   AND   a.indid=b.indid JOIN   sysobjects   c   ON   b.id=c.id  JOIN   syscolumns   d   ON   b.id=d.id   AND   b.colid=d.colid WHERE   a.indid   NOT IN(0,255) AND   c.name='col_comment_t2'  ORDER BY   c.name,a.name,d.name;
go

case 021 "新加列加列注释" 0
before:
drop table col_comment_t3;
go
src_sql:
create table dbo.col_comment_t3 (
	jioyrq	char(8) not null,
	jgjyls	char(14) not null,
	jczuho	int default 0,
	qjulsh	char(26),
	jiaoym	char(4),
	yxjlts	int default 0,
	sjchuo	char(17),
	jiluzt	char(1),
	record	int default 0,
	hxkbmc	char(30),
	sxjsri	char(8),
	fjxx01	char(30),
	byint1	int default 0,
	byint2	int default 0,
	bystr1	char(20),
	bystr2	char(20),
	primary key(jioyrq,jgjyls)
);
go
sleep(5000);
insert into dbo.col_comment_t3 values ('pfyrq001','pfyhjqjyls001',1,'上海英方有限公司！@#￥%001','2341',101,'This is a 测试','1',1011,'来自英方杭州分公司的测试','test1234',null,10111,101111,'浦发银行测试方案',' ');
insert into dbo.col_comment_t3 values ('pfyrq002','pfyhjqjyls002',2,'上海英方有限公司！@#￥%001','2342',102,'This is a 测试','2',1012,'来自英方杭州分公司的测试','test1234',null,10112,101112,'浦发银行测试方案','快乐健康六角');
ALTER TABLE dbo.col_comment_t3 ADD C_addcol1 varchar(50),c_Addcol2 numeric(18,12);
EXEC sp_addextendedproperty N'添加新列注释no1',N'~!@#$%^&*()_+|',N'SCHEMA',N'dbo',N'TABLE',N'col_comment_t3', N'COLUMN', N'C_addcol1';
EXEC sp_addextendedproperty N'添加新列注释no2',N'<>?:{}[]',N'SCHEMA',N'dbo',N'TABLE',N'col_comment_t3', N'COLUMN', N'c_Addcol2';
insert into dbo.col_comment_t3 values ('pfyrq003','pfyhjqjyls003',3,'上海英方有限公司！@#￥%002','2343',103,'This is a 测试','3',1013,'来自英方杭州分公司的测试','test1234',null,10113,101113,'浦发银行测试方案','快乐健康六角','新加列col1数据1','-176543.230000000981');
ALTER TABLE dbo.col_comment_t3 drop column c_Addcol2;
insert into dbo.col_comment_t3 values ('pfyrq004','pfyhjqjyls004',4,'上海英方有限公司！@#￥%002','2344',104,'This is a 测试','4',1014,'来自英方杭州分公司的测试','test1234',null,10113,101114,'浦发银行测试方案','快乐健康六角','新加列col1数据2');
update dbo.col_comment_t3 set qjulsh='#科技刻录机1234',jiluzt=1,hxkbmc=null where jioyrq='pfyrq010' and jgjyls='pfyhjqjyls001';
update dbo.col_comment_t3 set bystr2='雷科技skd',bystr1='刻录机刻录机';
go
tgt_sql:
select * from dbo.col_comment_t3 order by jczuho;
select class,class_desc,name,convert(nvarchar(255),value) from sys.extended_properties where major_id = OBJECT_ID('col_comment_t3') order by minor_id;
select name,xtype,length,isnullable from sys.syscolumns where id = OBJECT_ID('col_comment_t3');
select name,xtype from sys.sysobjects where parent_obj= OBJECT_ID('col_comment_t3') order by name;
select 索引名称=a.name ,表名=c.name ,索引字段名=d.name ,索引字段位置=d.colid  FROM  sysindexes   a JOIN   sysindexkeys   b   ON   a.id=b.id   AND   a.indid=b.indid JOIN   sysobjects   c   ON   b.id=c.id  JOIN   syscolumns   d   ON   b.id=d.id   AND   b.colid=d.colid WHERE   a.indid   NOT IN(0,255) AND   c.name='col_comment_t3'  ORDER BY   c.name,a.name,d.name;
go

case 022 "重命名注释列" 0
before:
drop table col_comment_t4;
go
src_sql:
create table dbo.col_comment_t4 (
	jioyrq	char(8) not null,
	jgjyls	char(14) not null,
	jczuho	int default 0,
	qjulsh	char(26),
	jiaoym	char(4),
	yxjlts	int default 0,
	sjchuo	char(17),
	jiluzt	char(1),
	record	int default 0,
	hxkbmc	char(30),
	sxjsri	char(8),
	fjxx01	char(30),
	byint1	int default 0,
	byint2	int default 0,
	bystr1	char(20),
	bystr2	char(20),
	primary key(jioyrq,jgjyls)
);
go
sleep(5000);
insert into dbo.col_comment_t4 values ('pfyrq001','pfyhjqjyls001',1,'上海英方有限公司！@#￥%001','2341',101,'This is a 测试','1',1011,'来自英方杭州分公司的测试','test1234',null,10111,101111,'浦发银行测试方案',' ');
insert into dbo.col_comment_t4 values ('pfyrq002','pfyhjqjyls002',2,'上海英方有限公司！@#￥%001','2342',102,'This is a 测试','2',1012,'来自英方杭州分公司的测试','test1234',null,10112,101112,'浦发银行测试方案','快乐健康六角');
ALTER TABLE dbo.col_comment_t4 ADD C_addcol1 varchar(50),c_Addcol2 numeric(18,12);
EXEC sp_addextendedproperty N'添加新列注释no3',N'~!@#$%^&*()_+|',N'SCHEMA',N'dbo',N'TABLE',N'col_comment_t4', N'COLUMN', N'C_addcol1';
EXEC sp_addextendedproperty N'添加新列注释no4',N'<>?:{}[]',N'SCHEMA',N'dbo',N'TABLE',N'col_comment_t4', N'COLUMN', N'c_Addcol2';
insert into dbo.col_comment_t4 values ('pfyrq003','pfyhjqjyls003',3,'上海英方有限公司！@#￥%002','2343',103,'This is a 测试','3',1013,'来自英方杭州分公司的测试','test1234',null,10113,101113,'浦发银行测试方案','快乐健康六角','新加列col1数据1','-176543.230000000981');
exec sp_rename 'dbo.col_comment_t4.C_addcol1','C_addcol1新列','COLUMN';
exec sp_rename 'dbo.col_comment_t4.c_Addcol2','新列c_Addcol2','COLUMN';
insert into dbo.col_comment_t4 values ('pfyrq004','pfyhjqjyls004',4,'上海英方有限公司！@#￥%002','2343',104,'This is a 测试','4',1014,'来自英方杭州分公司的测试','test1234',null,10114,101114,'浦发银行测试方案','快乐健康六角','新加列col1数据2','-176544.230000000981');
update dbo.col_comment_t4 set qjulsh='#科技刻录机1234',jiluzt=1,hxkbmc=null where jioyrq='pfyrq010' and jgjyls='pfyhjqjyls001';
update dbo.col_comment_t4 set bystr2='雷科技skd',bystr1='刻录机刻录机';
ALTER TABLE dbo.col_comment_t4 drop column 新列c_Addcol2;
go
tgt_sql:
select * from dbo.col_comment_t4 order by jczuho;
select class,class_desc,name,convert(nvarchar(255),value) from sys.extended_properties where major_id = OBJECT_ID('col_comment_t4') order by minor_id;
select name,xtype,length,isnullable from sys.syscolumns where id = OBJECT_ID('col_comment_t4');
select name,xtype from sys.sysobjects where parent_obj= OBJECT_ID('col_comment_t4') order by name;
select 索引名称=a.name ,表名=c.name ,索引字段名=d.name ,索引字段位置=d.colid  FROM  sysindexes   a JOIN   sysindexkeys   b   ON   a.id=b.id   AND   a.indid=b.indid JOIN   sysobjects   c   ON   b.id=c.id  JOIN   syscolumns   d   ON   b.id=d.id   AND   b.colid=d.colid WHERE   a.indid   NOT IN(0,255) AND   c.name='col_comment_t4'  ORDER BY   c.name,a.name,d.name;
go