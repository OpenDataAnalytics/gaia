# sudo docker build -t gaia .
# sudo docker run -it --rm -p 8888:8888 --hostname localhost gaia
# Find the URL in the console and open browser to that url

FROM jupyter/base-notebook

# Install jupyterlab widget manager (needed for custom widgets)
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager

# Install JupyterLab extension
RUN jupyter labextension install @johnkit/jupyterlab_geojs
RUN pip install jupyterlab_geojs

# Copy source files
ADD ./ /home/$NB_USER/gaia
USER root
RUN chown -R ${NB_UID}:${NB_UID} ${HOME}


# Install system dependencies
RUN sudo apt-get update
RUN sudo apt-get install --yes python-dev libblas-dev libgdal-dev liblapack-dev libatlas-base-dev gfortran


# Install python requirements (GDAL et al)
USER ${NB_USER}
WORKDIR /home/$NB_USER/gaia
RUN conda install --yes --file requirements.txt


# Install gaia
RUN pip install -r requirements.txt
RUN pip install -e .


# Setup entry point
WORKDIR /home/$NB_USER
EXPOSE 8888
CMD ["jupyter", "lab", "--ip", "0.0.0.0"]
