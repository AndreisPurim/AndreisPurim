import React from 'react';
import ReactDOM from 'react-dom/client';
import {
  createBrowserRouter,
  RouterProvider,
  Route,
  Link,
} from "react-router-dom";

import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/esm/Page/TextLayer.css";
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`;


const CustomPage = () => {
  const [numPages, setNumPages] = React.useState();
  const [pageNumber, setPageNumber] = React.useState(1);
  const [text, setText] = React.useState('');

  React.useEffect(()=>{

      
  }, [])

  const onDocumentLoadSuccess = async (e) => {
    setNumPages(e.numPages);
    //e.getPage(1)
    var a = await e.getPage(1)
    var b = await a.getTextContent()
    const pageText = b.items.map((item) => item.str).join(' ');
    console.log(pageText)
    setText(text)
  }

  return (
    <>
      <Document file={'sample.pdf'} onLoadSuccess={onDocumentLoadSuccess} />
      {text}
    </>
  );
};

// function CustomPage({ obj }){

//   const [numPages, setNumPages] = React.useState();
//   const [pageNumber, setPageNumber] = React.useState(1);

//   const onDocumentLoadSuccess = ({ numPages }) => {
//     setNumPages(numPages);
//     }

//   return (
//     <div>
//       asdasd
//       aaaa
//       <Document file="sample.pdf" onLoadSuccess={onDocumentLoadSuccess}>
//         <Page pageNumber={pageNumber} />
//       </Document>
//       aaaaaaaaaaaaaaaaaaa
//       <p>
//         Page {pageNumber} of {numPages}
//       </p>
//     </div>
//   );
// }

const files_manager = require('./files/files.json')

function App(){
  const [links, setLinks] = React.useState(null);

  React.useEffect(()=>{
      const links_list = [
        {
          path: "/",
          element: (
            <ul>
                {files_manager.map(link =>
                  <li key={link.name}>
                    <a href={"/"+link.name}>
                      {link.name}
                    </a>
                  </li>
                )
                }
            </ul>
          ),
        },
        ...files_manager.map(function(elem) {
          return {
            path: "/"+elem.name,
            element: <CustomPage obj={elem}/>
          }
        } 
        )
      ]
      setLinks(createBrowserRouter(links_list))
  }, [])


  return(
    <>
    {links? <RouterProvider router={links} />: null}
    </>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
