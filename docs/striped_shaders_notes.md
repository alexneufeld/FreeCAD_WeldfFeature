
The goal is to make striped lightweight tubes and cylinders like in solidworks weld bead features:

![](https://centralinnovation.com/wp-content/uploads/2022/03/wb.png)

We can use a vertex fragment shader to switch between one color and another based on the UV coordinates.

(example is unity shader code from [this blog post](https://andreashackel.de/blog/2017-10-03-stripes-shader-1/))

``` c#
fixed4 frag (v2f i) : SV_Target
{
	float pos = i.uv.x * 10;
	return floor(frac(pos) + 0.5);
}
```

This does require that the UV coordinate system has a basis that is aligned with the direction we want our stripes to face. Does that matter?

https://www.coin3d.org/Coin/html/classSoVRMLExtrusion.html

https://github.com/search?utf8=%E2%9C%93&q=SoVRMLExtrusion&type=code

https://github.com/mbsim-env/openmbv/blob/38f57c5e0947b9f9444ac26d5cd53397cbc6de99/openmbv/openmbv/coilspring.h#L26


some useful SoVRMLExtrusion snippets:

``` cpp
    case OpenMBV::CoilSpring::scaledTube: {
      auto *scaledTubeSep=new SoSeparator;
      soSep->addChild(scaledTubeSep);
      scale=new SoScale;
      scaledTubeSep->addChild(scale);
      auto *scaledExtrusion=new SoVRMLExtrusion;
      scaledTubeSep->addChild(scaledExtrusion);
      // cross section
      scaledExtrusion->crossSection.setNum(iCircSegments+1);
      SbVec2f *scs = scaledExtrusion->crossSection.startEditing();
      for(int i=0;i<iCircSegments;i++) // clockwise in local coordinate system
        scs[i]=SbVec2f(r*cos(i*2.*M_PI/iCircSegments), -r*sin(i*2.*M_PI/iCircSegments));
      scs[iCircSegments]=scs[0]; // close cross section: uses exact the same point: helpfull for "binary space partitioning container"
      scaledExtrusion->crossSection.finishEditing();
      scaledExtrusion->crossSection.setDefault(FALSE);
      // initialise spine
      scaledSpine = new float[3*(int(numberOfSpinePointsPerCoil*N)+1)];
      for(int i=0;i<=numberOfSpinePointsPerCoil*N;i++) {
        scaledSpine[3*i]= R*cos(i*N*2.*M_PI/numberOfSpinePointsPerCoil/N);
        scaledSpine[3*i+1]= R*sin(i*N*2.*M_PI/numberOfSpinePointsPerCoil/N);
        scaledSpine[3*i+2] = i*nominalLength/numberOfSpinePointsPerCoil/N;
      }
      scaledExtrusion->spine.setValuesPointer(int(numberOfSpinePointsPerCoil*N+1),scaledSpine);
      scaledExtrusion->spine.setDefault(FALSE);
      // additional flags
      scaledExtrusion->solid=TRUE; // backface culling
      scaledExtrusion->convex=TRUE; // only convex polygons included in visualisation
      scaledExtrusion->ccw=TRUE; // vertex ordering counterclockwise?
      scaledExtrusion->beginCap=TRUE; // front side at begin of the spine
      scaledExtrusion->endCap=TRUE; // front side at end of the spine
      scaledExtrusion->creaseAngle=1.5; // angle below which surface normals are drawn smooth (always smooth, except begin/end cap => < 90deg)
      break;
```

``` cpp
SoSeparator * Well::
makeExtrusion( SbVec3f to, float scaleFactor)
{
	// Group the attribute nodes and extrusion
	SoSeparator *pSep = new SoSeparator;
	int   numSides;
	int noPoints = getPoints(to);
	SbVec3f *temppoints = new SbVec3f[noPoints];
	memcpy(temppoints, points, noPoints*sizeof(points[0]));
	// Extrusion will be considered "solid" to enable back-face culling.
	// Also set crease angle to "smooth" surface for more than 4 sides.
	SoShapeHints *pHints = new SoShapeHints;
	pHints->vertexOrdering = SoShapeHints::COUNTERCLOCKWISE;
	pHints->shapeType = SoShapeHints::CONVEX;
	pHints->creaseAngle = (float)(M_PI / 2.1);
	pSep->addChild(pHints);
	SoVRMLExtrusion *pExt = new SoVRMLExtrusion;
	// Cross section (prescaled to diameter=1 to allow meaningful scaling)
	// 500 sides makes a very smooth cylinder .
	numSides = 500;
	int   side;
	float theta = 0.0f;
	float dTheta = (float)(2.0 * M_PI / (double)numSides);
	const float eps = 1e-6f;
	pExt->crossSection.setNum(numSides + 1);
	for (side = 0; side < numSides; side++) {
		float x = 0.5f * sin(theta);
		float z = 0.5f * cos(theta);
		if (fabs(x) < eps) x = 0;
		if (fabs(z) < eps) z = 0;
		pExt->crossSection.set1Value(side, SbVec2f(x, z));
		theta += dTheta;
	}
	//Bronze colour
	SoMaterial *bronze = new SoMaterial;
	bronze->ambientColor.setValue(.33, .22, .27);
	bronze->diffuseColor.setValue(.78, .57, .11);
	bronze->specularColor.setValue(.99, .94, .81);
	bronze->shininess = .28;
	pSep->addChild(bronze);
	pExt->crossSection.set1Value(numSides, SbVec2f(0, 0.5f));
	// Coordinates of well define the spine
	pExt->spine.setValues(0, noPoints, temppoints);
	pExt->scale.setNum(nPoints);
	// To make top side of well little larger than rest
	pExt->scale.set1Value(0, SbVec2f(scaleFactor+10, scaleFactor+10));
	//Defining radius for each coordinate values
	for (int i = 1; i <nPoints-2; ++i)
	{
		pExt->scale.set1Value(i, SbVec2f(scaleFactor, scaleFactor));
	}
	pExt->scale.set1Value(nPoints - 2, SbVec2f(scaleFactor + 4, scaleFactor + 4));
	pSep->addChild(pExt);
	return pSep;
}
```
