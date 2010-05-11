# Copyright (c) 2010 Derek Murray <derek.murray@cl.cam.ac.uk>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

'''
Created on 12 Apr 2010

@author: dgm36
'''
from mrry.mercator.cloudscript.interpreter import SWScheduler,\
    SW_THREAD_TERMINATOR, SWInterpreterTask
from mrry.mercator.cloudscript.context import SimpleContext
from mrry.mercator.cloudscript.parser import \
    SWStatementParser, SWExpressionParser
from threading import Condition, Thread
import traceback
import cmd

class SWInteractiveShell(cmd.Cmd):
    
    def __init__(self, num_threads=4):
        cmd.Cmd.__init__(self)
        self.scheduler = SWScheduler(num_threads)
        self.shell_context = SimpleContext()
    
        self.stmt_parser = SWStatementParser()
        self.expr_parser = SWExpressionParser()
    
        self.threads = []
        
        # Initialise task queue and worker thread pool.
        for i in range(0, num_threads):
            t = Thread(target=self.task_interpreter_main, args=())
            t.start()
            self.threads.append(t)
    
    def halt(self):
        self.scheduler.halt()
        for t in self.threads:
            t.join()
    
    def task_interpreter_main(self):
        while True:
            
            if not self.scheduler.is_running:
                break
            
            task = self.scheduler.run_queue.get()
            
            if task is SW_THREAD_TERMINATOR:
                break
            
            try:
                task.interpret()
            except Exception:
                traceback.print_exc()
                self.scheduler.halt()
    
    def do_print(self, arg):
        
        print "In do_print"
        
        stmt = self.stmt_parser.parse("return %s;" % arg)
        if stmt is None:
            self.stmt_parser.parser.restart()
            return
        
        eval_condvar = Condition()
        eval_task = SWInterpreterTask(self.scheduler, stmt, False, context=self.shell_context, condvar=eval_condvar)
        self.scheduler.add_task(eval_task)
    
        with eval_condvar:
            while not eval_task.done:
                eval_condvar.wait()
    
        print eval_task.result
        
        return False
    
    def default(self, line):
        
        print "In default"
        
        stmt = self.stmt_parser.parse(line)
        if stmt is None:
            self.stmt_parser.parser.restart()
            return
        
        eval_condvar = Condition()
        eval_task = SWInterpreterTask(self.scheduler, stmt, False, context=self.shell_context, condvar=eval_condvar)
        self.scheduler.add_task(eval_task)
        
        with eval_condvar:
            while not eval_task.done:
                eval_condvar.wait()
    
        return False
                
if __name__ == '__main__':
    shell = SWInteractiveShell()
    shell.cmdloop()
