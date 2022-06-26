/* This promela model was used to verify a past design of the bus object. */

bool lock = false;

inline enterMon() {
  atomic {
    !lock;
    lock = true;
  }
}

inline leaveMon() {
  lock = false;
}

typedef Condition {
  bool gate;
  byte waiting;
}

#define emptyC(C) (C.waiting == 0)

inline waitC(C) {
  atomic {
    C.waiting++;
    lock = false;
    C.gate;
    C.gate = false;
    C.waiting--;
  }
}

inline signalC(C) {
  atomic {
    if
      :: (C.waiting > 0) ->
         C.gate = true;
         !lock;
         lock = true;
      :: else
    fi;
  }
}

mtype = { clear, set };
mtype writing_event = clear;

byte critical = 0;
Condition done_writing;

bool live = false;

active proctype RX()
{
end:
  do
    :: enterMon();
       if
         :: (writing_event == set) ->
            waitC(done_writing);
         :: else
       fi;
       critical++;
       assert(critical == 1);
       live = true;
       live = false;
       critical--;
       leaveMon();
  od
}

active proctype TX()
{
end:
  do
    ::  atomic {
      writing_event == clear ->
      writing_event = set;
    }
       enterMon();
       critical++;
       assert(critical == 1);
       live = true;
       live = false;
       critical--;
       writing_event = clear;
       signalC(done_writing);
       leaveMon();
  od
}
ltl {[]<> live}
