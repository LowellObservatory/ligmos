[![Codacy Badge](https://api.codacy.com/project/badge/Grade/5a1444a2a46a45e2940837fa301d7fd1)](https://www.codacy.com/app/astrobokonon/ligmos?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=LowellObservatory/ligmos&amp;utm_campaign=Badge_Grade)

You'll definitely need:
- python 3.6 or greater.

Yes, really.  Python3.5 will fail because of the serviceping dependency!  Tough.

You'll also probably need:
- libffi-dev
- libssl-dev

for pynacl and cryptography dependencies to actually compile successfully.  
Find and install them in your particular way for your system.

But really, just use an Anaconda or Miniconda setup.

Then attept to actually install ligmos:
(in the source directory)

pip install -e .

and look for any compilation/installation failures for the dependencies.
