# dsImaging

## Introduction

The `dsImaging` package is a server-side DataSHIELD extension designed to facilitate the interaction with medical images in various formats within a secure DataSHIELD environment. It provides a comprehensive suite of functions that enable researchers to apply segmentation filters (masks) on images, as well as to utilize analysis models including feature extraction through radiomic feature extraction and 3D convolutional neural networks (3D CNN). This integration ensures that the analysis of medical images, such as CT scans, complies with the DataSHIELD security model, maintaining the privacy and security of the data.

Key features of the `dsImaging` package include:
- **Medical image processing:** Functions to interact with medical images in various formats, including DICOM and NIfTI.
- **Segmentation and analysis:** Tools to apply segmentation filters on images and to use analysis models for feature extraction.
- **Compliance with DataSHIELD security model:** Ensures that all image manipulations and analyses are performed in a way that adheres to the disclosure control measures set by DataSHIELD.
- **Integration with radiomics and computer vision:** Facilitates the application of advanced analysis models on medical images, enhancing the research capabilities within the DataSHIELD environment.

## Structure

The `dsImaging` ecosystem comprises two essential components designed to work in tandem: the server-side package (`dsImaging`) and the client-side package (`dsImagingClient`). Each component plays a pivotal role in the integration of medical imaging within the DataSHIELD environment. For comprehensive details on installation, setup, and usage, please refer to the respective repositories:

- **Server-Side package `dsImaging`**: This component is installed on the DataSHIELD server and is responsible for direct interactions with medical images in various formats. It provides functions for image processing, segmentation, and analysis, ensuring that all operations comply with the DataSHIELD security model. For code, installation instructions, and more, visit [https://github.com/isglobal-brge/dsImaging](https://github.com/isglobal-brge/dsImaging).

- **Client-Side package `dsImagingClient`**: Utilized by researchers and data analysts, this package facilitates the communication with the `dsImaging` package on the server. It sends image processing and analysis requests and receives results, ensuring a user-friendly experience for specifying analysis needs and parameters. For code, installation instructions, and more, visit [https://github.com/isglobal-brge/dsImagingClient](https://github.com/isglobal-brge/dsImagingClient).

## Installation

To install the server-side package `dsImaging`, follow the steps below. This guide assumes that you have administrative access to the DataSHIELD server and the necessary permissions to install R packages.

### Prerequisites

For the `dsImaging` package to function correctly, it is crucial to have a compatible Python environment set up on the DataSHIELD server. This setup is necessary because `dsImaging` utilizes the `reticulate` R package to integrate Python within the R environment, enabling the use of Python libraries and functions for masks application and radiomic feature extraction in medical imaging analysis. Administrators must ensure that Python is installed and properly configured on the server where `dsImaging` will be installed.

### Package installation

If you prefer using a graphical user interface (GUI) provided by your server for package installation, you can easily install the `dsImaging` package directly from GitHub. Navigate to the package installation section in your server's GUI, and specify the following details:

- **User/organization:** `isglobal-brge`
- **Package name:** `dsImaging`
- **Git reference:** `main`

#### Installing from the R console

If you are using an Opal server and have access to an administrator account, you can install the package from the R console using the `opalr` package. If you do not have the `opalr` package installed, you can install it using the following command:
```
install.packages("opalr")
```

To create a login object for the server, change the following code to match your specific server details and administrator credentials:
```
library(opalr)

# Change the URL and credentials to match your Opal server and administrator account!
o <- opal.login(username = "administrator", password = "password", url = "https://opal-demo.obiba.org/")
```

You can then install the `dsImaging` package using the following command:
```
dsadmin.install_github_package(o, 'dsImaging', username='isglobal-brge')
```

## Acknowledgements

- The development of dsImaging has been supported by the **[RadGen4COPD](https://github.com/isglobal-brge/RadGen4COPD)**, **[P4COPD](https://www.clinicbarcelona.org/en/projects-and-clinical-assays/detail/p4copd-prediction-prevention-personalized-and-precision-management-of-copd-in-young-adults)**, and **[DATOS-CAT](https://datos-cat.github.io/LandingPage)** projects. These collaborations have not only provided essential financial backing but have also affirmed the project's relevance and application in significant research endeavors.
- This project has received funding from the **[Spanish Ministry of Science and Innovation](https://www.ciencia.gob.es/en/)** and **[State Research Agency](https://www.aei.gob.es/en)** through the **“Centro de Excelencia Severo Ochoa 2019-2023” Program [CEX2018-000806-S]** and **[State Research Agency](https://www.aei.gob.es/en)** and **[Fondo Europeo de Desarrollo Regional, UE](https://ec.europa.eu/regional_policy/funding/erdf_en) (PID2021-122855OB-I00)**, and support from the **[Generalitat de Catalunya](https://web.gencat.cat/en/inici/index.html)** through the **CERCA Program** and **[Ministry of Research and Universities](https://recercaiuniversitats.gencat.cat/en/inici/) (2021 SGR 01563)**.

## Contact

For further information or inquiries, please contact:

- **Juan R González**: juanr.gonzalez@isglobal.org
- **David Sarrat González**: david.sarrat@isglobal.org
- **Xavier Escribà-Montagut**: xavier.escriba@isglobal.org

For more details about **DataSHIELD**, visit [https://www.datashield.org](https://www.datashield.org).

For more information about the **Barcelona Institute for Global Health (ISGlobal)**, visit [https://www.isglobal.org](https://www.isglobal.org).