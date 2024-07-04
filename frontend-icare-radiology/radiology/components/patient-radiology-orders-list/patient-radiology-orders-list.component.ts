import { HttpClient } from "@angular/common/http";
import { Component, Input, OnInit } from "@angular/core";
import { MatDialog } from "@angular/material/dialog";
import jsPDF from "jspdf";
import { SharedPdfPreviewComponent } from "src/app/shared/dialogs/shared-pdf-preview/shared-pdf-preview.component";
import { addBillStatusToOrders } from "src/app/shared/helpers/add-bill-status-to-ordered-items.helper";
import { OrdersService } from "src/app/shared/resources/order/services/orders.service";
import { VisitsService } from "src/app/shared/resources/visits/services";
import { FormBuilder } from '@angular/forms';

@Component({
  selector: "app-patient-radiology-orders-list",
  templateUrl: "./patient-radiology-orders-list.component.html",
  styleUrls: ["./patient-radiology-orders-list.component.scss"],
})
export class PatientRadiologyOrdersListComponent implements OnInit {
  @Input() currentUser: any;
  @Input() allUserRoles: any;
  @Input() userPrivileges: any;
  @Input() orders: any[];
  @Input() currentBills: any[];
  @Input() patientId: string;
  @Input() activeVisitUuid: string;
  @Input() activeVisit: any;
  outputurl:any;
  file: any;
  values: any = {};
  obsKeyedByConcepts: any = {};
  imagePreviews: { [key: string]: string } = {};
  saving: boolean = false;
  

  processedImagePreviews: { [key: string]: string } = {};
  

  base64FileData: any;
  formattedOrders: any[];

  constructor(
    private httpClient: HttpClient,
    private formBuilder: FormBuilder,
    private visitService: VisitsService,
    private ordersService: OrdersService,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    this.visitService
      .getVisitDetailsByVisitUuid(this.activeVisitUuid, {
        v: "custom:(encounters:(uuid,display,obs,orders,encounterDatetime,encounterType,location))",
      })
      .subscribe((response) => {
        if (response && response?.encounters?.length > 0) {
          response?.encounters?.forEach((encounter) => {
            encounter?.obs?.forEach((obs) => {
              this.obsKeyedByConcepts[obs?.concept?.uuid] = {
                ...obs,
                uri: obs?.value?.links && obs?.value?.links?.uri
                  ? obs?.value?.links?.uri?.replace("http", "https")
                  : null,
              };
            });
          });
        }
      });

    this.formattedOrders = addBillStatusToOrders(
      this.orders,
      this.currentBills,
      this.activeVisit
    );
  }

  previewPDFData(pdfData) {
    const doc = new jsPDF();
    doc.save("preview.pdf");
  }

  fileSelection(event: Event, order: any): void {
    event.stopPropagation();
    const fileInputElement = event.target as HTMLInputElement;
    if (fileInputElement.files && fileInputElement.files[0]) {
      this.file = fileInputElement.files[0];
      if (this.file.type.startsWith('image/')) {
        this.values[order.uuid] = this.file;
        const reader = new FileReader();
        reader.onload = () => {
          this.imagePreviews[order.uuid] = reader.result as string;
        };
        reader.readAsDataURL(this.file);
      } else {
        alert('Please select an image file');
      }
    }
  }
  processImage(event: any, order: any): void {
    event.stopPropagation();

    const file = this.values[order.uuid];
    if (!file || !file.type.startsWith('image/')) {
      alert('Please select a valid image file');
      return;
    }

    this.saving = true;

    const formData = new FormData();
    formData.append('file', file);

    this.httpClient.post<{ outputUrl: string }>('http://127.0.0.1:7002/image/', formData)
      .subscribe(
        (response) => {
          const outputUrl = `http://127.0.0.1:7002/processed/?filename=${response.outputUrl}`;
          // const outputUrl = `http://127.0.0.1:7002${response.outputUrl}`;
          console.log(`Processed image URL stored: ${outputUrl}`);
          this.outputurl = outputUrl;
          this.saving = false;
        },
        (error) => {
          console.error('Error:', error);
          this.saving = false;
          // alert('An error occurred while processing the image.');
        }
      );
  }

  // Function to retrieve processed image
  retrieveProcessedImage(): void {
    if (!this.outputurl) {
      console.error('No processed image URL available');
      return;
    }

    this.httpClient.get(this.outputurl, { responseType: 'blob' })
      .subscribe(
        (response: Blob) => {
          // Handle the retrieved image blob, e.g., display in UI or download
          console.log('Retrieved processed image:', response);
          const url = window.URL.createObjectURL(response);
          window.open(url);  // Opens the image in a new tab
        },
        (error) => {
          console.error('Error retrieving processed image:', error);
        }
      );
  }
}

//   getRemarks(event: any, order: any, outputUrl: string): void {
//      const comment = event?.target?.value;
//      const commentKey = `${order?.uuid}-comment`;

//   // Store comment and associated details in this.values
//   this.values[commentKey] = {
//     comment: comment,
//     disease: order?.disease,
//     outputUrl: outputUrl
//   };

//   // Clear comment field after storing
//   event.target.value = '';
// }
// }

// function getRemarks(event: Event, any: any, order: any, any1: any, outputUrl: any, string: any) {
//   throw new Error("Function not implemented.");
// }
//   onSave(event: Event, order: any): void {
//     event.stopPropagation();
//     this.saving = true;
//     let data = new FormData();
//     const jsonData = {
//       concept: order?.concept?.uuid,
//       person: this.patientId,
//       encounter: order?.encounterUuid,
//       obsDatetime: new Date(),
//       voided: false,
//       status: "PRELIMINARY",
//       order: order?.uuid,
//       comment: this.values[order?.uuid + "-comment"],
//     };
//     data.append("file", this.file);
//     data.append("json", JSON.stringify(jsonData));

//     // void first the existing observation
//     if (
//       this.obsKeyedByConcepts[order?.concept?.uuid] &&
//       this.obsKeyedByConcepts[order?.concept?.uuid]?.value
//     ) {
//       const existingObs = {
//         concept: order?.concept?.uuid,
//         person: this.patientId,
//         obsDatetime:
//           this.obsKeyedByConcepts[order?.concept?.uuid]?.encounter?.obsDatetime,
//         encounter:
//           this.obsKeyedByConcepts[order?.concept?.uuid]?.encounter?.uuid,
//         status: "PRELIMINARY",
//         comment:
//           this.obsKeyedByConcepts[order?.concept?.uuid]?.encounter?.comment,
//       };
//       this.httpClient
//         .post(
//           `../../../openmrs/ws/rest/v1/obs/${
//             this.obsKeyedByConcepts[order?.concept?.uuid]?.uuid
//           }`,
//           {
//             ...existingObs,
//             voided: true,
//           }
//         )
//         .subscribe((response) => {
//           if (response) {
//             this.saving = false;
//           }
//         });
//     }

//     const orders = [
//       {
//         uuid: order?.uuid,
//         fulfillerStatus: "RECEIVED",
//         encounter: order?.encounterUuid,
//       },
//     ];

//     this.ordersService
//       .updateOrdersViaEncounter(orders)
//       .subscribe((response) => {
//         this.saving = false;
//       });

//     this.httpClient
//       .post(`../../../openmrs/ws/rest/v1/obs`, data)
//       .subscribe((response: any) => {
//         if (response) {
//           this.obsKeyedByConcepts[order?.concept?.uuid] = {
//             ...response,
//             uri: response?.value?.links
//               ? response?.value?.links?.uri?.replace("http", "https")
//               : null,
//           };
//         }
//       });
//   }
// }

//   onSave(event: any, order: any): void {
//     event.stopPropagation();
  
//     // Save all activities and send to database
//     this.saving = true;
  
//     const dataToSave = {
//       // Add all activities data to be saved here
//       orders: this.formattedOrders,
//       remarks: this.obsKeyedByConcepts,
//       // Add other data to be saved here
//     };
  
//     this.httpClient.post('https://your-api-url.com/save-activities', dataToSave)
//       .subscribe(
//         (response) => {
//           console.log('Activities saved successfully');
//           this.saving = false;
//         },
//         (error) => {
//           console.error('Error:', error);
//           this.saving = false;
//           // alert('An error occurred while saving activities.');
//         }
//       );
//   }
// }