[1mdiff --git a/t_voice_api.py b/t_voice_api.py[m
[1mnew file mode 100644[m
[1mindex 00000000..c1c1370f[m
[1m--- /dev/null[m
[1m+++ b/t_voice_api.py[m
[36m@@ -0,0 +1,32 @@[m
[32m+[m
[32m+[m[32m                   SSUUMMMMAARRYY OOFF LLEESSSS CCOOMMMMAANNDDSS[m
[32m+[m
[32m+[m[32m      Commands marked with * may be preceded by a number, _N.[m
[32m+[m[32m      Notes in parentheses indicate the behavior if _N is given.[m
[32m+[m[32m      A key preceded by a caret indicates the Ctrl key; thus ^K is ctrl-K.[m
[32m+[m
[32m+[m[32m  h  H                 Display this help.[m
[32m+[m[32m  q  :q  Q  :Q  ZZ     Exit.[m
[32m+[m[32m ---------------------------------------------------------------------------[m
[32m+[m
[32m+[m[32m                           MMOOVVIINNGG[m
[32m+[m
[32m+[m[32m  e  ^E  j  ^N  CR  *  Forward  one line   (or _N lines).[m
[32m+[m[32m  y  ^Y  k  ^K  ^P  *  Backward one line   (or _N lines).[m
[32m+[m[32m  f  ^F  ^V  SPACE  *  Forward  one window (or _N lines).[m
[32m+[m[32m  b  ^B  ESC-v      *  Backward one window (or _N lines).[m
[32m+[m[32m  z                 *  Forward  one window (and set window to _N).[m
[32m+[m[32m  w                 *  Backward one window (and set window to _N).[m
[32m+[m[32m  ESC-SPACE         *  Forward  one window, but don't stop at end-of-file.[m
[32m+[m[32m  d  ^D             *  Forward  one half-window (and set half-window to _N).[m
[32m+[m[32m  u  ^U             *  Backward one half-window (and set half-window to _N).[m
[32m+[m[32m  ESC-)  RightArrow *  Right one half screen width (or _N positions).[m
[32m+[m[32m  ESC-(  LeftArrow  *  Left  one half screen width (or _N positions).[m
[32m+[m[32m  ESC-}  ^RightArrow   Right to last column displayed.[m
[32m+[m[32m  ESC-{  ^LeftArrow    Left  to first column.[m
[32m+[m[32m  F                    Forward forever; like "tail -f".[m
[32m+[m[32m  ESC-F                Like F but stop when search pattern is found.[m
[32m+[m[32m  r  ^R  ^L            Repaint screen.[m
[32m+[m[32m  R                    Repaint screen, discarding buffered input.[m
[32m+[m[32m        ---------------------------------------------------[m
[32m+[m[32m        Default "window" is the screen height.[m
