import React from 'react';
import ReactDOM from 'react-dom/client';
import {
  createBrowserRouter,
  RouterProvider,
  Route,
  Link,
} from "react-router-dom";

import { Document, Page } from 'react-pdf'
import { PDFDocument } from 'pdfjs-dist';
import { pdfjs } from 'react-pdf';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.js',
  import.meta.url,
).toString();

function CustomPage({ obj }){
  React.useEffect(()=>{
    fetch("./files/"+obj.link,{ responseType: 'arraybuffer',}
    ).then(function(res){
      const reader = new FileReader();
      console.log(res.data)
    })
      // const pdf = PDFDocument.load(res);
    //   const pages = pdf.getPages();
    //   let extractedText = '';

    //   for (const page of pages) {
    //     const textContent = page.getTextContent();
    //     const pageText = textContent.items.map((item) => item.str).join(' ');
    //     extractedText += pageText;
    //   }
    //   console.log(extractedText)
    // })
  })
  return(
    <>
      hey
      {obj.link}
    </>
  )
}

function App(){
  const [links, setLinks] = React.useState(null);

  React.useEffect(()=>{
    fetch("./files.json",{}
    ).then(function(res){
      return res.json()
    }).then(function(obj) {
      const links_list = [
        {
          path: "/",
          element: (
            <ul>
                {obj.files.map(link =>
                  <li>
                    <a href={"/"+link.name}>
                      {link.name}
                    </a>
                  </li>
                )
                }
            </ul>
          ),
        },
        ...obj.files.map(function(elem) {
          return {
            path: "/"+elem.name,
            element: <CustomPage obj={elem}/>
          }
        } 
        )
      ]
      console.log(links_list)
      setLinks(createBrowserRouter(links_list))
    })
  }, [])


  return(
    <>
    {links? <RouterProvider router={links} />: null}
    </>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
