
Wouldn't it be nice if we had a way of knowing which requirements and libraries were installed or not installed where ?
It is every so annoying to find your app working at home only to find that it breaks down on Travis just because
a library or a module was not included in the Pipfile.

The features designed are as below:

1. Find libraries installed in MAIN & libraries installed via PIPENV

2. Find where the dependencies are installed. Pathwise

3. Show Dependency Tree

4. Convert Pipfiles to Travis versions

__________________________

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Setup](#setup)
  - [Render your pset 4 repo](#render-your-pset-4-repo)
    - [Installations](#installations)
    - [AWS credentials](#aws-credentials)
  - [Styling Code](#styling-code)
    - [Fixing their work](#fixing-their-work)
  - [Create and populate an S3 bucket](#create-and-populate-an-s3-bucket)
    - [Pre-Trained Model & Input Content Image](#pre-trained-model--input-content-image)
  - [Limit builds on Travis](#limit-builds-on-travis)
- [Problems](#problems)
  - [A new atomic write](#a-new-atomic-write)
    - [New requirements](#new-requirements)
  - [External Tasks](#external-tasks)
  - [Copying S3 files locally](#copying-s3-files-locally)
  - [Stylizing](#stylizing)
    - [Option A) `ExternalProgramTask`](#option-a-externalprogramtask)
    - [Option B) Direct python](#option-b-direct-python)
  - [Running it via CI](#running-it-via-ci)
  - [Your Own Image](#your-own-image)
  - [(Optional) Up/Down](#optional-updown)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Setup

### Render your pset 4 repo

Using cookiecutter, as we've done in the past, navigate to the directory above
your local cookiecutter repo, and run:

```bash
cookiecutter cookiecutter-csci-pset-USERNAME/
```

With the following defaults, as you would expect:

| Param        | Value                                        |
| ------------ | -------------------------------------------- |
| project_name | `Pset 4`                                     |
| repo_name    | (should default to `2019fa-pset-4-USERNAME`) |

... etc

You can now perform your first push to github:

```bash
git init
git add --all
git commit -m "Add initial project skeleton."
git remote add origin git@github.com:csci-e-29/REPO_DIR.git
git fetch
git merge origin/master --allow-unrelated-histories
git push -u origin master
```

#### Installations

You will need luigi, pytorch, torchvision, and boto3 for this problem set.
Perform the following commands for the installations within your repo.

```bash
pipenv install luigi torch torchvision boto3
```

#### AWS credentials

As in previous problem sets, add your AWS credentials to an .env file as well as
in Travis settings.  Only make them available on the master branch.

### Styling Code

We will need the `neural_style` folder in the [pytorch
examples](https://github.com/pytorch/examples/tree/master/fast_neural_style)
repo. This contains the code necessary to stylize the image of our choosing. You
should clone or download the repo and manually place the `neural_style` package
into your repo (next to `pset_4`), committing it to your repo.

Grab the `download_saved_models.py` as well (you don't need to commit this).

Note that we are copying the 5 files into the `neural_style` as a separate
importable package next to the `pset_4` package.

It should look like:

```
<REPO>/
    pset_4/
        ...
    neural_style/
        __init__.py
        neural_style.py
        ...
    download_saved_models.py
    ...
```

#### Fixing their work
Depending on the solution you choose below, you may need to modify some of the
original code.  Here are two known issues:

1. The code does not use [relative
imports](https://realpython.com/absolute-vs-relative-python-imports/).  You may
need to modify `neural_style.py` to fix all imports to other modules in
`neural_style`.

2. The instructions indicate you should call `python
neural_style/neural_style.py`, but because this is executing a module inside a
package, you know this is incorrect. You can add a `__main__.py`, import `main`
from `neural_style.py`, and call it there, similar to your cookiecutter
template.  When done, you should be able to run the code directly via `python -m
neural_style`.

### Create and populate an S3 bucket

[Create an S3
bucket](https://docs.aws.amazon.com/AmazonS3/latest/gsg/CreatingABucket.html)
with any name you like.  You will be writing data to this bucket.

#### Pre-Trained Model & Input Content Image

Run `download_saved_models.py` to fetch the pretrained models locally. It will
fetch and extract data to `saved_models/`.  Do not commit these files.  Instead,
upload the `.pth` files to `s3://<your_bucket>/pset_4/saved_models/*`.  You may
do this manually in the S3 console or via the aws cli (or write Luigi code...
see optional section at end). Once uploaded, you can remove them from your local
disk!

Also grab this image:

![](http://images5.fanpop.com/image/photos/31300000/Luigi-at-Mario-Party-luigi-31330265-220-229.jpg)

... and upload it to `s3://<bucket>/pset_4/images/luigi.jpg`.

***Ensure `data/` is in your `.gitignore`!*** You should not commit anything
*besides python code and other text files.

S3 will be the source of truth for data - you read everything from S3 (even if
you had it stored locally first).

### Limit builds on Travis

Because we're pulling a bit more data and running things with a bit more
computation, ***ensure you only download models and run stylization on master***
for your Travis builds. You should minimize the commits there as well; try to
get everything working locally on develop or a feature branch before releasing
to master.

## Problems

Let's get started on our [Luigi](https://luigi.readthedocs.io/en/stable/)
workflow.

One way of structuring your code is to have all Luigi tasks isolated.  Create a
sub-package `pset_4.tasks` for this purpose.  This should contain very little
other code, but may import whatever it needs.

### A new atomic write

NB: if you get stuck on this part, you can continue the other sections by using
`Target.path` non-atomically before coming back to finish this.

Luigi implements atomic writing quite well within its `Target` classes.
However, one feature it does not handle is preserving the suffix of the output
target in the temporary file.  This will be a problem for this pset, because we
will be using image utilities that determine the file format from the extension.

In `csci_utils`, create a new module `csci_utils.luigi.target` with something
like the following:

```python
from luigi.local_target import LocalTarget, atomic_file


class suffix_preserving_atomic_file(atomic_file):
    def generate_tmp_path(self, path):
        ...


class BaseAtomicProviderLocalTarget(LocalTarget):
    # Allow some composability of atomic handling
    atomic_provider = atomic_file

    def open(self, mode='r'):
        # leverage super() as well as modifying any code in LocalTarget
        # to use self.atomic_provider rather than atomic_file
        ...

    @contextmanager
    def temporary_path(self):
        # NB: unclear why LocalTarget doesn't use atomic_file in its implementation
        self.makedirs()
        with self.atomic_provider(self.path) as af:
            yield af.tmp_path


class SuffixPreservingLocalTarget(BaseAtomicProviderLocalTarget):
    atomic_provider = suffix_preserving_atomic_file
```

#### New requirements

Note that luigi is now a dependency of csci_utils.  You should update the
setup.py to reflect that.  Consider if you want it to always depend on luigi, or
use
[extras_require](https://setuptools.readthedocs.io/en/latest/setuptools.html#declaring-extras-optional-features-with-their-own-dependencies).

If you do use `extras_require`, a neat trick is:

```python
extras = {...}
extras['all'] = ... # Take the set of all extras, and sort into a list

setup(
    ...
    extras_require=extras,
)
```

... and ensure your library development pipfile simply includes the extras with
`csci_utils = {extras = ["all"]...}` or `pipenv install -e .[all]` or similar.

### External Tasks

Note that we are essentially trying to run the following "Stylize" command:

```bash
python neural_style/neural_style.py eval --content-image </path/to/content/image> --model </path/to/saved/model> --output-image </path/to/output/image> --cuda 0
```

Think about the dependency graph:

- We have a model on S3 (s3://<bucket>/pset_4/saved_models/rain_princess.pth)
- We have an input image on S3 (s3://<bucket>/pset_4/images/luigi.jpg)
- We have to stylize the image given the pre-trained model

For each of the two first points, create a [Luigi External
Task](https://luigi.readthedocs.io/en/stable/api/luigi.task.html#luigi.task.ExternalTask)
that represents the [S3
target](https://luigi.readthedocs.io/en/stable/api/luigi.contrib.s3.html#luigi.contrib.s3.S3Target)
where those files are located.

You should keep these together in a submodule named `pset_4.tasks.data`. These
should be `ExternalTask`'s since we never run them - rather the files should
have just been provided.

`pset_4.tasks.data`:

```python
import os

from luigi import ExternalTask, Parameter, Task
from luigi.contrib.s3 import S3Target


class ContentImage(ExternalTask):
    IMAGE_ROOT = ... # Root S3 path, as a constant

    # Name of the image
    image = Parameter(...) # Filename of the image under the root s3 path

    def output(self):
        # return the S3Target of the image


class SavedModel(ExternalTask):
    MODEL_ROOT = ...

    model = Parameter(...) # Filename of the model

    def output(self):
        # return the S3Target of the model
```

***NB***: Luigi treats binary files differently than the standard
`open(mode='wb')`. You should use the `format` kwarg to any `Target` and use
`luigi.format.Nop` to indicate a binary file you might read or write directly.
Otherwise, luigi will assume it can open the file in text mode.  If you see
errors related to unicode decoding, it's because you need to specify the format.

To test that Luigi can find the files, you can run the following:

```bash
luigi --module pset_4.tasks.data ContentImage --local-scheduler --image luigi.jpg
```

... or add the following code to `main` in `pset_4.cli` and run `python -m
pset_4`:

```python
build([
    ContentImage(
        image='luigi.jpg'
    )], local_scheduler=True)
```

### Copying S3 files locally

Ideally, we wouldn't need to copy files locally - we could read directly from
the remote.  However, to cut down on bandwidth and to simplify the interfacing
code, we'll cache the files and models locally.

In `pset_4.tasks.data`, use a luigi `Task` to perform this functionality.

What is the general pattern here?  Try to restructure and/or commit some code to
`csci_utils` rather than solving this copy problem uniquely for this pset.

```python
class DownloadModel(Task):
    S3_ROOT = 's3://...'
    LOCAL_ROOT = os.path.abspath('data')
    SHARED_RELATIVE_PATH = 'saved_models'

    model = ... #luigi parameter

    def requires(self):
        # Depends on the SavedModel ExternalTask being complete
        # i.e. the file must exist on S3 in order to copy it locally
        ...

    def output(self):
        ...

    def run(self):
        # Use self.output() and self.input() targets to atomically copy
        # the file locally!

class DownloadImage(Task):
    S3_ROOT = 's3://...'
    LOCAL_ROOT = os.path.abspath('data')
    SHARED_RELATIVE_PATH = 'images'

    image = ... # Luigi parameter

    def requires(self):
        # Depends on the ContentImage ExternalTask being complete

    def output(self):
        ...

    def run(self):
        # Use self.output() and self.input() targets to atomically copy
        # the file locally!
```

Again you can run this via, for example:

```bash
luigi --module pset_4.tasks.data DownloadImage --local-scheduler
```

***DO NOT CALL `DownloadImage().run()` directly***.  This will bypass the
scheduler and ignore the dependencies, etc.

Also, note that once luigi successfully writes an output, the task will not
rerun unless you delete that file!  If you made a mistake, delete the output
file, change the code, and rerun.

### Stylizing

Now let's create a task that does the equivalent of the following in luigi:

```bash
python neural_style/neural_style.py eval --content-image </path/to/content/image> --model </path/to/saved/model> --output-image </path/to/output/image> --cuda 0
```

You have two options for implementing this.  Both will require some structure
within `pset_4.tasks.stylize`:

```python
import luigi
from csci_utils.luigi.target import SuffixPreservingLocalTarget
from .data import DownloadModel, DownloadImage

class Stylize(...):
    model = ...
    image = ...

    def requires(self):
        return {
            'image': ...,
            'model': ...
        }

    def output(self):
        # return SuffixPreservingLocalTarget of the stylized image
```

In both cases, you need to ensure the output is written atomically.  You may
want to consider [using
target.temporary_path()](https://luigi.readthedocs.io/en/stable/api/luigi.target.html#luigi.target.FileSystemTarget.temporary_path).

#### Option A) `ExternalProgramTask`

This will entail an
[ExternalProgramTask](https://luigi.readthedocs.io/en/stable/api/luigi.contrib.external_program.html#luigi.contrib.external_program.ExternalProgramTask).

For a good example of this executed, see this [blog
post](https://markhneedham.com/blog/2017/03/25/luigi-externalprogramtask-example-converting-json-csv/).

```python
from luigi.contrib.external_program import ExternalProgramTask

class Stylize(ExternalProgramTask):
    ...
    def program_args(self):
        # Be sure to use self.temp_output_path
        return ['python', ...]

    def run(self):
        # You must set up an atomic write!
        # (use self.output().path if you can't get that working)
        with self.output().temporary_path() as self.temp_output_path:
            super().run()
```

#### Option B) Direct python

Directly call, copy, or modify the code in `neural_style.neural_style.stylize`:

```python
from neural_style.neural_style import stylize

class Stylize(Task):
    ...
    def run(self):
        # For example
        inputs = self.input()
        with self.output().temporary_path() as temp_output_path:
            class args:
                content_image = inputs['image'].path
                output_image = temp_output_path
                ...
            stylize(args)
```

### Running it via CI

So that travis can test this via `python -m pset_4`, ensure you run `build` with
`local_scheduler=True` within the `main()` function of `pset4.cli`.  Travis
should run `luigi.jpg` with any of the models.

Optionally, you can add parameterization via argparse to help you play around
with your own image and varying styles.  Something like:

```python
from luigi import build

from .tasks.stylize import Stylize

parser = ...
parser.add_argument("-i", "--image", default=...)
parser.add_argument("-m", "--model", default=...)


def main(args=None):
    ...
    build([
        ...
    ], local_scheduler=True)
```

Note that for testing purposes, you can also do the following with the same
functionality:

```bash
luigi --module pset_4.tasks.stylize Stylize --local-scheduler
```

### Your Own Image

Instead of the image provided, find a new image of your choosing! You are going
to stylize it.

Note that it should not be too large - native size images from cell phones (eg
8mp) will take a long time to render and may not look good.  You can resize the
image (manually, using any tool you wish, or using `pillow` in your repo) to
about 500px on the longest edge.

You may pick any of the pretrained models for styling.

Add your image to S3 and run the pipeline to stylize your image.

We will not run CI/CD for your image.  Run it locally and upload the result to
the answers quiz.  ***Never commit an image or model to git***.

### (Optional) Up/Down

We did something funny above - copied data locally, pushed to S3, and then
wrote code to pull back from s3!  Why did we go to the trouble?

Local data is ephemeral and not meant to be shared.  You cannot treat it as an
archive or immutable source of truth.  If you swap computers (or work with
someone else, or need to run on a remote server/Travis...) you cannot always
'just' share the data.  We must treat the ***remote*** data as the originating
source.

This, however, does not mean we can't write more intelligent code!

For both your content images and pretrained models, modify your tasks to look
something like:

```python
class ContentImage(ExternalTask):
    # This should now be a local target!
    ...

class UploadImage(Task):
    # Push image to S3 if it doesn't already exist
    ...

class DownloadImage(Task):
    # output target should be identical to ContentImage!
    ...
```

Due to the way Luigi works, it will skip uploading/downloading if the image
already exists locally.  It will also skip upload if it finds the image in S3,
so Travis and new jobs will work just fine (so long as the images are uploaded).

Try to think of the best way to generalize a solution!
