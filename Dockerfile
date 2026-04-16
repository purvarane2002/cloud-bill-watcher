FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY src/handler.py ${LAMBDA_TASK_ROOT}

CMD ["handler.lambda_handler"]