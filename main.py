import os
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'compare')))
import compare
import ergodic


print(os.getcwd())

p=compare.ergodic_database()
print(compare.config)
src = 'sqlserver';tgt = 'postgre';err_handling = 3
dump_excel = ergodic.get_casefile()
p.compare(src, tgt, err_handling)
print(compare.config)
p.dump_e()
