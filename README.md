[![Codacy Badge](https://app.codacy.com/project/badge/Grade/300ef9d970c44328bde4d1c0a0d68a74)](https://www.codacy.com/gh/LowellObservatory/ligmos/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=LowellObservatory/ligmos&amp;utm_campaign=Badge_Grade)

You'll definitely need:
- python 3.6 or greater.

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
