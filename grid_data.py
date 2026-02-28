import pandas as pd
import streamlit as st
from st_aggrid import JsCode, AgGrid, GridOptionsBuilder

df=pd.DataFrame([{"orgHierarchy": 'A', "jobTitle": "CEO", "employmentType": "Permanent" },
    { "orgHierarchy": 'A/B', "jobTitle": "VP", "employmentType": "Permanent" }])
st.write(df)
gb = GridOptionsBuilder.from_dataframe(df)
gridOptions = gb.build()


gridOptions["columnDefs"]= [
    { "field": 'jobTitle' },
    { "field": 'employmentType' },
]

gridOptions["defaultColDef"]={
      "flex": 1,
    },
gridOptions["autoGroupColumnDef"]= {
    "headerName": 'Organisation Hierarchy',
    "minWidth": 300,
    "cellRendererParams": {
      "suppressCount": True,
    },
  },
gridOptions["treeData"]=True
gridOptions["animateRows"]=True
gridOptions["groupDefaultExpanded"]= -1
gridOptions["getDataPath"]=JsCode(""" function(data){
    return data.orgHierarchy.split("/");
  }""").js_code

r = AgGrid(
    df,
    gridOptions=gridOptions,
    height=500,
    allow_unsafe_jscode=True,
    enable_enterprise_modules=True,
    filter=True,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    theme="material",
    tree_data=True
)
