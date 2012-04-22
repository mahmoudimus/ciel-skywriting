from setuptools import setup

setup(
    name = "ciel-skywriting",
    version = '0.1-dev',
    description = "Scripting language for distributed, parallel computation",
    author = "Derek Murray",
    author_email = "Derek.Murray@cl.cam.ac.uk",
    url = "http://www.cl.cam.ac.uk/netos/ciel/skywriting/",
    packages = [ 'swi', 'swi.stdlib' ],
    package_dir = { '' : 'src/python' },
    entry_points = {'console_scripts' : ['skywriting=swi.interpreter:main', 'sw-job=swi.submit:main'],
                    'ciel.executor.plugin' : ['swi=swi.executor:load']},
    data_files = [ ("lib/ciel/skywriting/stdlib/",
                   ["src/python/swi/stdlib/%s" %s for s in
                     ["environ", "grab", "java", "mapreduce",
                      "stdinout", "sync"]])],
    classifiers = [
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: ISC License (ISCL)',
            'Operating System :: POSIX',
            'Topic :: Software Development :: Interpreters',
            'Topic :: System :: Distributed Computing',
        ],
    requires=['ciel (>=0.1)', 'ply']
)

