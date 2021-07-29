import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='emo_recognition_bot',
    author='Fedor Lisin',
    author_email='theo.lisin@gmail.com',
    description='Voice emotion recognition telegram bot',
    keywords='bot, wav2vec, telegram',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/TheoLisin/Emotion_Recognition_with_Wav2Vec',
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    classifiers=[
        # see https://pypi.org/classifiers/
        "Development Status :: 1 - Alpha",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
        "Programming Language :: Python :: 3.8"
    ],
    python_requires='>=3.6',
    install_requires=['torch', 'torchaudio', 'aiogram', 'asyncio', 'datasets', 'transformers', 'logging', 'numpy', ],
    entry_points={
        'console_scripts': [              
            'emo_bot=emo_recognition_bot.emo_bot:main',
        ],
    },
)